from .city import city
from .fetch import fetch
from .forecast import forecast
from .history import history
from .pollutant import pollutant
from .sensor import sensor
from .train import train


def register_blueprints(app):
    app.register_blueprint(city)
    app.register_blueprint(fetch)
    app.register_blueprint(forecast)
    app.register_blueprint(history)
    app.register_blueprint(pollutant)
    app.register_blueprint(sensor)
    app.register_blueprint(train)
