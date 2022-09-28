from flask import Flask

from api.blueprints.cities import cities_blueprint
from api.blueprints.countries import countries_blueprint
from api.blueprints.errors import errors_blueprint
from api.blueprints.forecast import forecast_blueprint
from api.blueprints.history import history_blueprint
from api.blueprints.icon import icon_blueprint
from api.blueprints.pollutants import pollutants_blueprint
from api.blueprints.sensors import sensors_blueprint

__all__ = [
    "cities_blueprint",
    "countries_blueprint",
    "errors_blueprint",
    "forecast_blueprint",
    "history_blueprint",
    "icon_blueprint",
    "pollutants_blueprint",
    "sensors_blueprint"
]


def register_blueprints(app: Flask) -> None:
    for blueprint in __all__:
        app.register_blueprint(globals()[blueprint], url_prefix="/api/v1")
