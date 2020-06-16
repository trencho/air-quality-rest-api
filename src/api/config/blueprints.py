from api.resources.cities import cities
from api.resources.fetch import fetch
from api.resources.forecast import forecast
from api.resources.history import history
from api.resources.pollutant import pollutant
from api.resources.sensors import sensors
from api.resources.train import train

__all__ = [
    'cities',
    'fetch',
    'forecast',
    'history',
    'pollutant',
    'sensors',
    'train'
]


def register_blueprints(app):
    for blueprint in __all__:
        app.register_blueprint(globals()[blueprint], url_prefix='/api')
