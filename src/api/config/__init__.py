import os

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from definitions import mongo_db_host_env_value, mongo_db_name_env_value, mongo_db_user_name_env_value, \
    mongo_db_user_pass_env_value, OPEN_API_VERSION
from .blueprints import register_blueprints
from .db import mongo
from .environment import check_environment_variables, fetch_mongodb_data
from .schedule import schedule_fetch_date, schedule_model_training
from .swagger import swagger


def schedule_operations():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=schedule_fetch_date, trigger='interval', hours=1)
    scheduler.add_job(func=schedule_model_training, trigger='cron', year='*', month='*', day='last')

    scheduler.start()


def create_app():
    # Comment these 2 lines to skip the environment variable check and scheduling of api operations when running app in
    # debug mode
    check_environment_variables()
    schedule_operations()

    app = Flask(__name__)

    register_blueprints(app)

    # Comment these 6 lines for the mongodb when running app in debug mode
    app.config['MONGO_URI'] = ('mongodb+srv://' + os.environ.get(mongo_db_user_name_env_value) + ':'
                               + os.environ.get(mongo_db_user_pass_env_value) + '@'
                               + os.environ.get(mongo_db_host_env_value) + '/' + os.environ.get(mongo_db_name_env_value)
                               + '?retryWrites=true&w=majority')
    mongo.init_app(app)
    fetch_mongodb_data()

    app.config['SWAGGER'] = {
        'openapi': OPEN_API_VERSION
    }
    swagger.init_app(app)

    return app
