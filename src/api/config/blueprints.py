from api.blueprints.cities import cities
from api.blueprints.forecast import forecast
from api.blueprints.history import history
from api.blueprints.pollutants import pollutant
from api.blueprints.sensors import sensors

__all__ = [
    'cities',
    # 'fetch',
    'forecast',
    'history',
    'pollutant',
    'sensors',
    # 'train'
]


def register_blueprints(app):
    for blueprint in __all__:
        app.register_blueprint(globals()[blueprint], url_prefix='/api')
