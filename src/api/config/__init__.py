import os

from flask import Flask

from .blueprints import register_blueprints
from .db import mongo
from .swagger import swagger


def create_app():
    app = Flask(__name__)

    register_blueprints(app)
    # Comment the 4 lines for the mongodb when running app in debug mode
    app.config['MONGO_URI'] = ('mongodb+srv://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD']
                               + '@' + os.environ['MONGODB_HOSTNAME'] + '/' + os.environ['MONGODB_DATABASE']
                               + '?retryWrites=true&w=majority')
    mongo.init_app(app)

    app.config['SWAGGER'] = {
        'openapi': '3.0.3'
    }
    swagger.init_app(app)

    return app
