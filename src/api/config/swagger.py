from logging import getLogger

from flasgger import Swagger
from flask import Flask

from definitions import URL_PREFIX

logger = getLogger(__name__)

CONFIG = {
    "favicon": f"{URL_PREFIX}/favicon.ico/",
    "openapi": "3.0.3",
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": f"{URL_PREFIX}/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": f"{URL_PREFIX}/flasgger_static",
    "specs_route": f"{URL_PREFIX}/apidocs/",
    "title": "AQRA"
}

swagger = Swagger(config=CONFIG, merge=True)


def configure_swagger(app: Flask) -> None:
    swagger.init_app(app)
    logger.info("Swagger configured successfully")
