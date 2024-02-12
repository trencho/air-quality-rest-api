from logging import getLogger

from flask import Flask, jsonify, make_response, Response
from flask_healthz import Healthz
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from definitions import URL_PREFIX
from .cache import cache
from .schedule import scheduler

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
    logger.info(f"Scheduler state: {scheduler.state}")
    if scheduler.state != 1:
        scheduler.start()
        return make_response(jsonify(message="SERVICE_UNAVAILABLE"), HTTP_503_SERVICE_UNAVAILABLE)

    return jsonify(message="OK")
