from flasgger import Swagger

from definitions import OPEN_API_VERSION

swagger = Swagger()


def configure_swagger(app):
    app.config['SWAGGER'] = {
        'openapi': OPEN_API_VERSION
    }
    swagger.init_app(app)
