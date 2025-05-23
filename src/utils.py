import time
from functools import wraps
from logging import getLogger

logger = getLogger(__name__)


def track_time(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"Function {func.__name__} took {end - start} seconds to run")
        return result

    return wrapper
