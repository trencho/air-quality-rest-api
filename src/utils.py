import time
from enum import Enum
from functools import wraps
from logging import getLogger
from typing import Iterable, Iterator

logger = getLogger(__name__)


class BatchOutcome(Enum):
    """What one unit of work in a batch job achieved.

    Returned by the functions that isolate their own failures, so the loop driving them
    can tell the three apart. A bare ``bool`` cannot: "nothing to do" and "it worked" are
    both truthy, and conflating them is how a job that trained no models at all reports
    the same thing as one that trained every model it had.
    """

    DONE = "done"
    SKIPPED = "skipped"
    FAILED = "failed"


class BatchTally:
    """Counts what a batch job actually achieved and says so when the loop ends.

    Every loop in this project isolates its items: one bad sensor is logged and the run
    moves on to the next one. That is the right behaviour and it stays. But it means a job
    in which every single item failed finishes exactly like a job in which every item
    succeeded -- neither raises, both exit 0, and the only difference is a pile of
    tracebacks that nothing was counting.

    It is a context manager so the summary cannot be forgotten, and so that it survives
    the job raising partway through::

        with BatchTally(logger, "fetch_locations", "country") as tally:
            for country in tally.track(countries):
                try:
                    ...
                except Exception:
                    tally.failure(f"Could not update {country['countryName']}")

    A context manager rather than a self-summarising generator, specifically because the
    loops here nest -- city, then sensor, then collection. ``track`` on the innermost
    iterable is re-entered once per sensor, so a generator that summarised on exhaustion
    would fire once per sensor rather than once per job. ``__exit__`` fires exactly once
    however deep the nesting goes.

    Severity escalates with the damage: a clean run is ``info``, some failures are
    ``warning``, and *everything* failing is ``error``, because a job that achieved
    nothing is a different event from a job that dropped one sensor.
    """

    def __init__(self, log, job: str, unit: str, plural: str = None):
        self._logger = log
        self._job = job
        self._unit = unit
        # Passed rather than derived. A `unit + "s"` rule renders "city" as "citys", and
        # the fix for that is a pluralisation function that will be wrong about the next
        # word instead. One optional argument at three call sites is cheaper and correct.
        self._plural = plural or f"{unit}s"
        self._summarised = False
        self.total = 0
        self.failures = 0
        self.skipped = 0

    def __enter__(self) -> "BatchTally":
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        # Summarise even when the job is unwinding: "died after 12 of 400 sensors" is the
        # most useful line in that log, and it is the one that would go missing.
        self.summarise()
        return False

    @property
    def done(self) -> int:
        return self.total - self.failures - self.skipped

    def track(self, items: Iterable) -> Iterator:
        """Yield each item, counting it as attempted."""
        for item in items:
            self.attempt()
            yield item

    def attempt(self) -> None:
        """Count one unit, for a loop whose iterable is not the unit being tallied."""
        self.total += 1

    def failure(self, message: str) -> None:
        """Log the exception being handled and count the unit as failed."""
        self._logger.exception(message)
        self.failures += 1

    def record(self, outcome: BatchOutcome) -> None:
        """Count an outcome a callee already decided (and already logged)."""
        if outcome is BatchOutcome.FAILED:
            self.failures += 1
        elif outcome is BatchOutcome.SKIPPED:
            self.skipped += 1

    def summarise(self) -> None:
        """Emit the one line that says whether this job accomplished anything."""
        if self._summarised:
            return
        self._summarised = True

        unit = self._unit if self.total == 1 else self._plural
        if not self.total:
            self._logger.info(f"{self._job}: no {unit} to process")
            return

        detail = f"{self.done} done, {self.failures} failed"
        if self.skipped:
            detail += f", {self.skipped} skipped"
        summary = f"{self._job}: {self.total} {unit} -- {detail}"

        if not self.failures:
            self._logger.info(summary)
        elif self.failures == self.total:
            # Not a warning. Every unit failing means the job achieved nothing, which is
            # the case this class exists to make visible.
            self._logger.error(f"{summary} (every {self._unit} failed)")
        else:
            self._logger.warning(summary)


def format_duration(seconds):
    """Converts seconds into a human-readable format."""
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    parts = []
    if days:
        parts.append(f"{int(days)}d")
    if hours:
        parts.append(f"{int(hours)}h")
    if minutes:
        parts.append(f"{int(minutes)}m")
    parts.append(f"{sec:.2f}s")

    return " ".join(parts)


def track_time(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        duration = end - start
        readable_duration = format_duration(duration)
        logger.info(f"Function {func.__name__} took {readable_duration} seconds to run")
        return result

    return wrapper
