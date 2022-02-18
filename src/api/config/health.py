from flask import Flask, jsonify, make_response, Response
from flask_healthz import Healthz
from starlette.status import HTTP_200_OK

HEALTHZ = {
    'live': 'config.health.liveness'
}


def configure_healthcheck(app: Flask) -> None:
    app.config['HEALTHZ'] = HEALTHZ
    Healthz(app, no_log=True)


def liveness() -> Response:
    return make_response(jsonify(error_message='OK'), HTTP_200_OK)
