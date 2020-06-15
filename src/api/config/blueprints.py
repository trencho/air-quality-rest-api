from api.resources.city import city
from api.resources.fetch import fetch
from api.resources.forecast import forecast
from api.resources.history import history
from api.resources.pollutant import pollutant
from api.resources.sensor import sensor
from api.resources.train import train

__all__ = [
    'city',
    'fetch',
    'forecast',
    'history',
    'pollutant',
    'sensor',
    'train'
]


def register_blueprints(app):
    for blueprint in __all__:
        app.register_blueprint(globals()[blueprint], url_prefix='/api')
