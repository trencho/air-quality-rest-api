from flask import Flask

from api.blueprints.cities import cities_blueprint
from api.blueprints.countries import countries_blueprint
from api.blueprints.errors import errors_blueprint
from api.blueprints.forecast import forecast_blueprint
from api.blueprints.history import history_blueprint
from api.blueprints.icon import icon_blueprint
from api.blueprints.plots import plots_blueprint
from api.blueprints.pollutants import pollutants_blueprint
from api.blueprints.sensors import sensors_blueprint
from definitions import URL_PREFIX


def register_blueprints(app: Flask) -> None:
    blueprints = [
        cities_blueprint,
        countries_blueprint,
        errors_blueprint,
        forecast_blueprint,
        history_blueprint,
        icon_blueprint,
        plots_blueprint,
        pollutants_blueprint,
        sensors_blueprint,
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint, url_prefix=URL_PREFIX)
