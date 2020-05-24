import os

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from definitions import OPEN_API_VERSION
from definitions import mongo_db_host_env_value, mongo_db_name_env_value, mongo_db_port_env_value, \
    mongo_db_user_name_env_value, mongo_db_user_pass_env_value
from .blueprints import register_blueprints
from .db import mongo
from .environment import check_environment_variables
from .schedule import schedule_fetch_date
from .swagger import swagger

__all__ = [
    'schedule_fetch_date'
]


def schedule_operations():
    for operation in __all__:
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=globals()[operation], trigger='interval', hours=1)


def create_app():
    # Comment these 2 lines to skip the environment variable check and scheduling of api operations
    # when running app in debug mode
    check_environment_variables()
    schedule_operations()

    app = Flask(__name__)

    register_blueprints(app)

    # Comment these 5 lines for the mongodb when running app in debug mode
    app.config['MONGO_URI'] = ('mongodb://' + os.environ.get(mongo_db_user_name_env_value) + ':'
                               + os.environ.get(mongo_db_user_pass_env_value) + '@'
                               + os.environ.get(mongo_db_host_env_value) + ':' + os.environ.get(mongo_db_port_env_value)
                               + '/' + os.environ.get(mongo_db_name_env_value) + '?retryWrites=true&w=majority')
    mongo.init_app(app)

    app.config['SWAGGER'] = {
        'openapi': OPEN_API_VERSION
    }
    swagger.init_app(app)

    return app
