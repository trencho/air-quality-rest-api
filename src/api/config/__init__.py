from os import environ

from flask import Flask

from definitions import app_dev, app_env, app_prod
from .blueprints import register_blueprints
from .cache import configure_cache
from .cors import configure_cors
from .database import configure_database
from .environment import check_environment_variables, fetch_data, init_system_paths
from .health import configure_healthcheck
from .logger import configure_logger
from .schedule import model_training, schedule_jobs
from .swagger import configure_swagger


def create_app() -> Flask:
    init_system_paths()

    app = Flask(__name__)

    if environ.get(app_env, app_dev) == app_prod:
        check_environment_variables()
        schedule_jobs(app)

    register_blueprints(app)

    configure_cache(app)
    configure_cors(app)

    try:
        configure_database(app)
    except Exception:
        pass

    configure_healthcheck(app)
    configure_logger()
    configure_swagger(app)

    fetch_data()

    return app
