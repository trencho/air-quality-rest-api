"""Tests for ``utils.BatchTally`` — the end-of-job line that says what a batch achieved.

Every scheduled job here isolates its items: one bad sensor is logged and the run moves
on. That is correct and it stays. The consequence is that a job in which every item failed
finishes exactly like a job in which every item succeeded — neither raises, both exit 0,
and the only difference is a pile of tracebacks nothing was counting.

So the assertions below are mostly about **severity**, not arithmetic. Getting the counts
right and logging them all at ``info`` would leave the situation exactly as it was: a line
nobody reads. The escalation to ``error`` when everything failed is the feature.
"""

from logging import getLogger

import pytest

from utils import BatchOutcome, BatchTally

_LOGGER_NAME = "tests.batch_tally"


@pytest.fixture
def log():
    return getLogger(_LOGGER_NAME)


def _summary(caplog):
    """The single summary record, asserting there is exactly one."""
    records = [r for r in caplog.records if r.name == _LOGGER_NAME]
    assert len(records) == 1, f"expected one summary, got {len(records)}"
    return records[0]


def test_reports_an_empty_batch_as_having_nothing_to_do(log, caplog):
    # Distinct from "everything failed" on purpose: a job with no work is not a broken job,
    # and collapsing the two is what makes an alert on this line useless.
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with BatchTally(log, "fetch_locations", "city", "cities") as tally:
            for _ in tally.track([]):
                pass

    record = _summary(caplog)
    assert record.levelname == "INFO"
    assert "no cities to process" in record.message


def test_reports_a_clean_run_at_info(log, caplog):
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with BatchTally(log, "fetch_locations", "city", "cities") as tally:
            for _ in tally.track(["skopje", "bitola", "ohrid"]):
                pass

    record = _summary(caplog)
    assert record.levelname == "INFO"
    assert "3 cities" in record.message
    assert "3 done, 0 failed" in record.message


def test_reports_a_partial_failure_at_warning(log, caplog):
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with BatchTally(log, "fetch_locations", "city", "cities") as tally:
            for city in tally.track(["skopje", "bitola", "ohrid"]):
                if city == "bitola":
                    try:
                        raise RuntimeError("upstream refused")
                    except RuntimeError:
                        tally.failure(f"Could not update {city}")

    records = [r for r in caplog.records if r.name == _LOGGER_NAME]
    # The per-item traceback and the summary: the summary replaces neither.
    assert len(records) == 2
    failure, summary = records
    assert failure.levelname == "ERROR"
    assert failure.exc_info is not None, "the per-item traceback must survive"
    assert summary.levelname == "WARNING"
    assert "2 done, 1 failed" in summary.message


def test_escalates_to_error_when_every_unit_failed(log, caplog):
    # The whole point. A job that achieved nothing is a different event from a job that
    # dropped one sensor, and only this line can say so.
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with BatchTally(log, "fetch_locations", "city", "cities") as tally:
            for city in tally.track(["skopje", "bitola"]):
                try:
                    raise RuntimeError("upstream is down")
                except RuntimeError:
                    tally.failure(f"Could not update {city}")

    summary = [r for r in caplog.records if r.name == _LOGGER_NAME][-1]
    assert summary.levelname == "ERROR"
    assert "0 done, 2 failed" in summary.message
    assert "every city failed" in summary.message


def test_counts_skipped_units_apart_from_done_ones(log, caplog):
    # "47 models, 0 failed" reads as success while every one of them was skipped. Keeping
    # skips in their own column is what stops that.
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with BatchTally(log, "model_training", "model") as tally:
            for outcome in tally.track(
                [BatchOutcome.DONE, BatchOutcome.SKIPPED, BatchOutcome.SKIPPED]
            ):
                tally.record(outcome)

    summary = _summary(caplog)
    assert summary.levelname == "INFO"
    assert "1 done, 0 failed, 2 skipped" in summary.message


def test_record_counts_a_failure_a_callee_already_logged(log, caplog):
    # `record` must not log again: the callee that returned FAILED already wrote the
    # traceback, and a second copy makes the log harder to read, not more informative.
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with BatchTally(log, "model_training", "model") as tally:
            for outcome in tally.track([BatchOutcome.FAILED, BatchOutcome.DONE]):
                tally.record(outcome)

    summary = _summary(caplog)
    assert summary.levelname == "WARNING"
    assert "1 done, 1 failed" in summary.message


def test_summarises_when_the_job_dies_partway_through(log, caplog):
    # "died after 12 of 400 sensors" is the most useful line in that log, and it is exactly
    # the one an explicit call after the loop would lose.
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with pytest.raises(RuntimeError):
            with BatchTally(log, "import_data", "file") as tally:
                for index in tally.track(range(10)):
                    if index == 3:
                        raise RuntimeError("the disk went away")

    summary = _summary(caplog)
    assert "4 files" in summary.message


def test_summarises_once_even_if_asked_twice(log, caplog):
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with BatchTally(log, "import_data", "file") as tally:
            for _ in tally.track(["a.csv"]):
                pass
            tally.summarise()

    _summary(caplog)  # asserts exactly one record


def test_uses_the_singular_for_a_single_unit(log, caplog):
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with BatchTally(log, "import_data", "file") as tally:
            for _ in tally.track(["only.csv"]):
                pass

    assert "1 file --" in _summary(caplog).message


def test_attempt_counts_a_unit_that_is_not_the_loop_variable(log, caplog):
    # fetch_hourly_data tallies collections while looping over sensors, so the unit and the
    # iterable are different things.
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with BatchTally(log, "fetch_hourly_data", "collection") as tally:
            for _ in ["sensor-1", "sensor-2"]:
                for _ in ["weather", "pollution"]:
                    tally.attempt()
                    tally.record(BatchOutcome.DONE)

    assert "4 collections" in _summary(caplog).message


def test_the_plural_is_passed_not_guessed(log, caplog):
    # A `unit + "s"` rule renders "city" as "citys". The default still applies to the
    # regular units, which is why both halves are pinned here rather than only the
    # irregular one.
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with BatchTally(log, "fetch_locations", "city", "cities") as tally:
            for _ in tally.track(["skopje", "bitola"]):
                pass
    assert "2 cities" in _summary(caplog).message

    caplog.clear()
    with caplog.at_level("INFO", logger=_LOGGER_NAME):
        with BatchTally(log, "import_data", "file") as tally:
            for _ in tally.track(["a.csv", "b.csv"]):
                pass
    assert "2 files" in _summary(caplog).message
