from flasgger import Swagger
from flask import Flask

config = {
    "favicon": "/favicon.ico/",
    "openapi": "3.0.3",
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/api/v1/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/api/v1/flasgger_static",
    "specs_route": "/api/v1/apidocs/",
    "title": "AQRA"
}
swagger = Swagger(config=config, merge=True)


def configure_swagger(app: Flask) -> None:
    swagger.init_app(app)
