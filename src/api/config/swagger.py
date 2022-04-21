from flasgger import Swagger
from flask import Flask

config = Swagger.DEFAULT_CONFIG
config['favicon'] = '/api/v1/favicon.ico/'
config['openapi'] = '3.0.3'
config['specs'] = [
    {
        'endpoint': 'apispec_1',
        'route': '/api/v1/apispec_1.json',
        'rule_filter': lambda rule: True,
        'model_filter': lambda tag: True,
    }
]
config['static_url_path'] = '/api/v1/flasgger_static'
config['specs_route'] = '/api/v1/apidocs/'
config['title'] = 'AQRA'
swagger = Swagger(config=config)


def configure_swagger(app: Flask) -> None:
    swagger.init_app(app)
