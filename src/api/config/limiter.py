from os import environ

from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from definitions import (
    APP_ENV,
    ENV_DEV,
    ENV_PROD,
    METRICS_PATH,
    RATE_LIMIT_DEFAULTS,
    RATE_LIMIT_STORAGE_URI,
    REDIS_URL,
    URL_PREFIX,
)


def _storage_uri() -> str:
    # A dedicated override wins; otherwise share the Redis backend when one is
    # configured; otherwise in-process memory (dev / single worker).
    return environ.get(RATE_LIMIT_STORAGE_URI) or environ.get(REDIS_URL) or "memory://"


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=RATE_LIMIT_DEFAULTS,
    storage_uri=_storage_uri(),
    swallow_errors=True,  # a storage-backend hiccup must not 500 the request
)


@limiter.request_filter
def _exempt_monitoring_endpoints() -> bool:
    # Health probes (k8s) and the Prometheus scrape endpoint are hit frequently and
    # must never be throttled.
    return (
        request.path.startswith(f"{URL_PREFIX}/healthz") or request.path == METRICS_PATH
    )


def init_limiter(app: Flask) -> None:
    if environ.get(APP_ENV, ENV_DEV) == ENV_PROD:
        # In prod the app sits behind nginx over a unix socket, so request.remote_addr
        # is the socket peer, not the client. Trust one proxy's X-Forwarded-For header
        # (set by nginx) so the limiter keys on the real client IP.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
    limiter.init_app(app)
