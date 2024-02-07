from atexit import register
from json import load
from logging import getHandlerByName, getLogger
from logging.config import dictConfig
from os import path

from definitions import LOG_PATH

logger = getLogger(__name__)


def configure_logger() -> None:
    config_file = path.join(path.dirname(path.abspath(__file__)), "logging_configs", "config.json")
    with open(config_file) as in_file:
        config_dict = load(in_file)

    file_handler_config = config_dict.get("handlers", {}).get("file", {})
    # Check if the necessary keys are present
    if "filename" in file_handler_config:
        # Update the filename in the configuration
        file_handler_config["filename"] = path.join(LOG_PATH, "app.log")

    dictConfig(config_dict)
    queue_handler = getHandlerByName("queue")
    if queue_handler is not None:
        queue_handler.listener.start()
        register(queue_handler.listener.stop)
