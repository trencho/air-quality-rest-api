import time
from functools import wraps
from logging import getLogger

logger = getLogger(__name__)


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
