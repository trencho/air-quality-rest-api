from flasgger import Swagger
from flask import Flask

config = {
    'openapi': '3.0.3',
    'specs': [
        {
            'endpoint': 'apispec_1',
            'route': '/api/v1/apispec_1.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True,
        }
    ],
    'specs_route': '/api/v1/apidocs/'}
swagger = Swagger(config=config, merge=True)


def configure_swagger(app: Flask) -> None:
    swagger.init_app(app)
