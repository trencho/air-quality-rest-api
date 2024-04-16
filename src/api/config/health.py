from logging import getLogger

from flask import Flask, jsonify, Response
from flask_healthz import Healthz

from definitions import URL_PREFIX
from .cache import cache

logger = getLogger(__name__)

HEALTHZ = {
    "live": "api.config.health.liveness",
    "ready": "api.config.health.readiness",
}


def configure_healthcheck(app: Flask) -> None:
    app.config["HEALTHZ"] = HEALTHZ
    Healthz(app, prefix=f"{URL_PREFIX}/healthz", no_log=True)


@cache.cached(timeout=180)
def liveness() -> Response:
    return jsonify(message="OK")


@cache.cached(timeout=180)
def readiness() -> Response:
    return jsonify(message="OK")
