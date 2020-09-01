from api.blueprints.cities import cities_blueprint
from api.blueprints.forecast import forecast_blueprint
from api.blueprints.history import history_blueprint
from api.blueprints.pollutants import pollutants_blueprint
from api.blueprints.sensors import sensors_blueprint

__all__ = [
    'cities_blueprint',
    # 'fetch_blueprint',
    'forecast_blueprint',
    'history_blueprint',
    'pollutants_blueprint',
    'sensors_blueprint'
    # 'train_blueprint'
]


def register_blueprints(app):
    for blueprint in __all__:
        app.register_blueprint(globals()[blueprint], url_prefix='/api/v1')
