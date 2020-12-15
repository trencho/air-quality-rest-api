from flask import Flask

from .blueprints import register_blueprints
from .cache import configure_cache
from .database import configure_database
from .environment import check_environment_variables, fetch_db_data
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

    # Comment these 2 lines to skip the mongodb configuration when running application in debug mode
    configure_database(app)
    fetch_db_data()

    # Comment this line to skip training regression models for all available locations during application startup
    model_training()

    configure_swagger(app)

    return app
