from logging import Formatter, getLogger, INFO, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from os import path
from sys import stdout

from definitions import LOG_PATH

logger = getLogger()


def configure_logger() -> None:
    logger.setLevel(INFO)
    formatter = Formatter("%(asctime)s %(name)-30s %(levelname)-8s %(message)s")
    file_handler = TimedRotatingFileHandler(path.join(LOG_PATH, "app.log"), when="midnight", backupCount=5)
    file_handler.setFormatter(formatter)
    std_out_handler = StreamHandler(stdout)
    std_out_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(std_out_handler)
