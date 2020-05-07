import os

from flask import Flask

from .blueprints import register_blueprints
from .db import mongo
from .swagger import swagger


def create_app():
    app = Flask(__name__)

    register_blueprints(app)
    # Comment the 3 lines for the mongodb when running app in debug mode
    app.config['MONGO_URI'] = ('mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD']
                               + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_DATABASE'])
    mongo.init_app(app)
    swagger.init_app(app)

    return app
