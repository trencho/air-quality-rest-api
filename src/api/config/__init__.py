from flask import Flask

from .blueprints import register_blueprints
from .db import mongo, configure_database
from .environment import check_environment_variables, fetch_db_data
from .schedule import schedule_jobs
from .swagger import swagger, configure_swagger


def create_app():
    # Comment these 2 lines to skip the environment variable check and scheduling of api operations when running app in
    # debug mode
    check_environment_variables()
    schedule_jobs()

    app = Flask(__name__)

    register_blueprints(app)

    # Comment these 2 lines for the mongodb configuration when running app in debug mode
    configure_database(app)
    fetch_db_data()

    configure_swagger(app)

    return app
