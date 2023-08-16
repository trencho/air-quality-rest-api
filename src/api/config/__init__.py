from os import environ

from flask import Flask

from definitions import APP_DEV, APP_ENV, APP_PROD
from .blueprints import register_blueprints
from .cache import configure_cache
from .cors import configure_cors
from .environment import check_environment_variables, fetch_data, init_system_paths
from .health import configure_healthcheck
from .logger import configure_logger
from .schedule import model_training
from .swagger import configure_swagger


def create_app() -> Flask:
    init_system_paths()

    app = Flask(__name__)

    if environ.get(APP_ENV, APP_DEV) == APP_PROD:
        check_environment_variables()

    register_blueprints(app)

    configure_cache(app)
    configure_cors(app)
    configure_healthcheck(app)
    configure_logger()
    configure_swagger(app)

    fetch_data()

    return app
