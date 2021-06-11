from flasgger import Swagger

config = {
    'openapi': '3.0.3',
    'specs': [
        {
            'endpoint': 'apispec_1',
            'route': '/api/v1/apispec_1.json',
            'rule_filter': lambda rule: True,  # all in
            'model_filter': lambda tag: True,  # all in
        }
    ],
    'specs_route': '/api/v1/apidocs/'}
swagger = Swagger(config=config, merge=True)


def configure_swagger(app):
    swagger.init_app(app)
