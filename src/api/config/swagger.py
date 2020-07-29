from flasgger import Swagger

swagger = Swagger()


def configure_swagger(app):
    app.config['SWAGGER'] = {
        'openapi': '3.0.3'
    }
    swagger.init_app(app)
