from flask import Flask
from flask_cors import CORS

from definitions import URL_PREFIX


def init_cors(app: Flask) -> None:
    CORS(app, resources=rf"{URL_PREFIX}/*")
