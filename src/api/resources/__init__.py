from .city import city
from .fetch import fetch
from .forecast import forecast
from .history import history
from .pollutant import pollutant
from .sensor import sensor
from .train import train

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
        app.register_blueprint(globals()[blueprint])
