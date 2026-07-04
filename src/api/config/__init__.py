from os import environ

from flask import Flask

from definitions import ENV_DEV, APP_ENV, ENV_PROD, SKIP_DATA_FETCH
from .blueprints import init_blueprints
from .cache import init_cache
from .converters import init_converters
from .cors import init_cors
from .environment import init_environment_variables, init_data, init_system_paths
from .garbage_collection import init_gc
from .health import init_healthcheck
from .logger import init_logger
from .schedule import init_scheduler
from .swagger import init_swagger


def create_app() -> Flask:
    init_logger()
    init_gc()
    init_system_paths()

    app = Flask(__name__)

    if environ.get(APP_ENV, ENV_DEV) == ENV_PROD:
        init_environment_variables()
        init_scheduler()

    init_converters(app)
    init_blueprints(app)

    init_cache(app)
    init_cors(app)
    init_healthcheck(app)
    init_swagger(app)

    if environ.get(SKIP_DATA_FETCH, "").lower() not in ("1", "true", "yes"):
        init_data()

    return app
