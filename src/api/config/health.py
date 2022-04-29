from flask import Flask, jsonify, make_response, Response
from flask_healthz import Healthz
from starlette.status import HTTP_200_OK

from .cache import cache


def configure_healthcheck(app: Flask) -> None:
    app.config['HEALTHZ'] = {'live': 'api.config.health.liveness'}
    Healthz(app, no_log=True)


@cache.cached(timeout=0)
def liveness() -> Response:
    return make_response(jsonify(error_message='OK'), HTTP_200_OK)
