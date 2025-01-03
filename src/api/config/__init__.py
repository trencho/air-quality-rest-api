from os import environ

from flask import Flask

from definitions import ENV_DEV, APP_ENV, ENV_PROD
from .blueprints import register_blueprints
from .cache import configure_cache
from .converters import configure_converters
from .cors import configure_cors
from .environment import check_environment_variables, fetch_data, init_system_paths
from .garbage_collection import configure_gc
from .health import configure_healthcheck
from .logger import configure_logger
from .schedule import configure_scheduler
from .swagger import configure_swagger


def create_app() -> Flask:
    configure_gc()
    init_system_paths()
    configure_logger()

    app = Flask(__name__)

    if environ.get(APP_ENV, ENV_DEV) == ENV_PROD:
        check_environment_variables()
        configure_scheduler()

    configure_converters(app)
    register_blueprints(app)

    configure_cache(app)
    configure_cors(app)
    configure_healthcheck(app)
    configure_swagger(app)

    fetch_data()

    return app
