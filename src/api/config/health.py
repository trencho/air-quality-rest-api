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

CACHE_TIMEOUT = 180  # Cache timeout in seconds


def configure_healthcheck(app: Flask) -> None:
    app.config["HEALTHZ"] = HEALTHZ
    Healthz(app, prefix=f"{URL_PREFIX}/healthz", no_log=True)
    logger.info("Health check configured with endpoints: /live and /ready")


@cache.cached(timeout=CACHE_TIMEOUT)
def liveness() -> Response:
    logger.info("Liveness check called")
    return jsonify(message="OK")


@cache.cached(timeout=CACHE_TIMEOUT)
def readiness() -> Response:
    logger.info("Readiness check called")
    return jsonify(message="OK")
