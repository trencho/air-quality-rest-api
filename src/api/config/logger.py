from atexit import register
from logging import getHandlerByName
from logging.config import dictConfig
from os import path

from definitions import LOG_PATH

CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s [%(name)]-30s [%(process)d] [%(levelname)]-10s %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]"
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": f"{path.join(LOG_PATH, "app.log")}",
            "when": "midnight",
            "backupCount": 5
        },
        "queue": {
            "class": "logging.handlers.QueueHandler",
            "handlers": [
                "stdout",
                "file"
            ],
            "respect_handler_level": True
        }
    },
    "loggers": {
        "root": {
            "handlers": [
                "queue"
            ],
            "level": "DEBUG",
            "propagate": True
        }
    }
}


def configure_logger() -> None:
    dictConfig(CONFIG)
    queue_handler = getHandlerByName("queue")
    if queue_handler is not None:
        queue_handler.listener.start()
        register(queue_handler.listener.stop)
