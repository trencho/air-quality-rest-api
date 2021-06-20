from os import environ

from flask import Flask

from definitions import mongodb_connection
from .blueprints import register_blueprints
from .cache import configure_cache
from .database import configure_database
from .environment import check_environment_variables, fetch_data
from .schedule import model_training, schedule_jobs
from .swagger import configure_swagger


def create_app():
    # Comment these 2 lines to skip the environment variable check and scheduling of api operations when running
    # application in debug mode
    check_environment_variables()
    schedule_jobs()

    app = Flask(__name__)

    register_blueprints(app)

    configure_cache(app)

    if environ.get(mongodb_connection) is not None:
        configure_database(app)

    configure_swagger(app)

    fetch_data()

    # Comment this line to skip training regression models for all available locations during application startup
    model_training()

    return app
