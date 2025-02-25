from logging import getLogger

from flasgger import Swagger
from flask import Flask

from definitions import URL_PREFIX

logger = getLogger(__name__)

FAVICON_URL = f"{URL_PREFIX}/favicon.ico/"
OPENAPI_VERSION = "3.0.3"
SPECS_ENDPOINT = "apispec_1"
SPECS_ROUTE = f"{URL_PREFIX}/apispec_1.json"
STATIC_URL_PATH = f"{URL_PREFIX}/flasgger_static"
APIDOCS_ROUTE = f"{URL_PREFIX}/apidocs/"
TITLE = "AQRA"

CONFIG = {
    "favicon": FAVICON_URL,
    "openapi": OPENAPI_VERSION,
    "specs": [
        {
            "endpoint": SPECS_ENDPOINT,
            "route": SPECS_ROUTE,
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": STATIC_URL_PATH,
    "specs_route": APIDOCS_ROUTE,
    "title": TITLE
}

swagger = Swagger(config=CONFIG, merge=True)


def configure_swagger(app: Flask) -> None:
    swagger.init_app(app)
    logger.info("Swagger configured successfully")
