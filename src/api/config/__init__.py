from os import environ

from flask import Flask

from definitions import app_dev, app_env, app_prod, mongodb_connection
from .blueprints import register_blueprints
from .cache import configure_cache
from .database import configure_database
from .environment import check_environment_variables, fetch_data
from .health import configure_healthcheck
from .schedule import model_training, schedule_jobs
from .swagger import configure_swagger


def create_app() -> Flask:
    if environ.get(app_env, app_dev) == app_prod:
        check_environment_variables()
        schedule_jobs()

    app = Flask(__name__)

    register_blueprints(app)

    configure_cache(app)

    if environ.get(mongodb_connection) is not None:
        configure_database(app)

    configure_healthcheck(app)

    configure_swagger(app)

    fetch_data()

    return app
