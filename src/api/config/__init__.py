from flask import Flask

from .db import mongo
from .routes import register_blueprints
from .swagger import swagger


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['MONGO_URI'] = ('mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD']
                               + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_DATABASE'])
    mongo.init_app(app)
    swagger.init_app(app)

    return app
