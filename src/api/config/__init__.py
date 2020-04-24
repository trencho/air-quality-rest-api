from flask import Flask
from flask_cors import CORS

from api.resources import register_blueprints
from .db import mongo
from .swagger import swagger


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['MONGO_URI'] = 'mongodb://localhost:27017/local'
    mongo.init_app(app)
    swagger.init_app(app)
    register_blueprints(app)

    return app
