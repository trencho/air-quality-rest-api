from atexit import register
from logging import getHandlerByName, getLogger
from logging.config import dictConfig
from os import makedirs

from definitions import LOG_PATH

LOG_LEVEL_INFO = "INFO"

CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s [%(name)s] [%(process)d] [%(levelname)s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL_INFO,
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": LOG_LEVEL_INFO,
            "formatter": "simple",
            "filename": f"{LOG_PATH / 'app.log'}",
            "when": "midnight",
            "backupCount": 5,
        },
        "queue": {
            "class": "logging.handlers.QueueHandler",
            "handlers": ["stdout", "file"],
            "respect_handler_level": True,
        },
    },
    "loggers": {"root": {"handlers": ["queue"], "level": "DEBUG", "propagate": True}},
}


def init_logger() -> None:
    makedirs(LOG_PATH, exist_ok=True)
    dictConfig(CONFIG)
    queue_handler = getHandlerByName("queue")
    if queue_handler is not None:
        queue_handler.listener.start()
        register(queue_handler.listener.stop)
    getLogger(__name__).info("Logger configured successfully")
