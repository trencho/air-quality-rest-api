from logging import Formatter, getLogger, INFO, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from os import path
from sys import stdout

from definitions import LOG_PATH

log = getLogger()


def configure_logger() -> None:
    log.setLevel(INFO)
    formatter = Formatter('%(asctime)s %(name)-30s %(levelname)-8s %(message)s')
    file_handler = TimedRotatingFileHandler(path.join(LOG_PATH, 'app.log'), when='midnight', interval=1, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.suffix = '%Y%m%d'
    std_out_handler = StreamHandler(stdout)
    std_out_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    log.addHandler(std_out_handler)
