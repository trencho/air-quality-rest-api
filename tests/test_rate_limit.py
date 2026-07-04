"""Hermetic tests for rate limiting (``api.config.limiter``).

The shared limiter is disabled for the rest of the suite (see ``conftest.py``); these
tests re-enable it on throwaway apps and assert enforcement + the health-check
exemption. Each test resets the in-memory buckets after wiring the app so the shared
client IP doesn't leak request counts.
"""

import pytest
from flask import Flask

# Import the config package first so the api chain initialises in order.
import api.config  # noqa: F401
from api.blueprints.errors import errors_blueprint
from api.config.limiter import _storage_uri, init_limiter, limiter
from definitions import RATE_LIMIT_STORAGE_URI, REDIS_URL, URL_PREFIX


@pytest.fixture
def active_limiter():
    was_enabled = limiter.enabled
    limiter.enabled = True
    yield
    limiter.enabled = was_enabled


def test_rate_limit_returns_429_after_limit(active_limiter):
    app = Flask(__name__)

    @app.route("/ping")
    @limiter.limit("2 per minute")
    def _ping():
        return "ok"

    init_limiter(app)
    limiter.reset()  # storage exists once init_app has run; clear leaked counts
    client = app.test_client()

    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 429


def test_health_checks_are_exempt_from_limits(active_limiter):
    app = Flask(__name__)

    @app.route(f"{URL_PREFIX}/healthz/live")
    @limiter.limit("1 per minute")
    def _live():
        return "ok"

    @app.route("/data")
    @limiter.limit("1 per minute")
    def _data():
        return "ok"

    init_limiter(app)
    limiter.reset()
    client = app.test_client()

    # A normal route is limited after its allowance...
    assert client.get("/data").status_code == 200
    assert client.get("/data").status_code == 429
    # ...but the health path is exempt no matter how often it is hit.
    for _ in range(3):
        assert client.get(f"{URL_PREFIX}/healthz/live").status_code == 200


def test_rate_limited_response_is_429_with_error_blueprint(active_limiter):
    # The real app registers the errors blueprint, whose catch-all handler must not
    # turn the limiter's 429 into a 500 (the bug the end-to-end check caught).
    app = Flask(__name__)
    app.register_blueprint(errors_blueprint)

    @app.route("/guarded")
    @limiter.limit("1 per minute")
    def _guarded():
        return "ok"

    init_limiter(app)
    limiter.reset()
    client = app.test_client()

    assert client.get("/guarded").status_code == 200
    assert client.get("/guarded").status_code == 429


def test_storage_uri_prefers_override_then_redis_then_memory(monkeypatch):
    monkeypatch.delenv(RATE_LIMIT_STORAGE_URI, raising=False)
    monkeypatch.delenv(REDIS_URL, raising=False)
    assert _storage_uri() == "memory://"

    monkeypatch.setenv(REDIS_URL, "redis://shared:6379")
    assert _storage_uri() == "redis://shared:6379"

    monkeypatch.setenv(RATE_LIMIT_STORAGE_URI, "redis://dedicated:6379")
    assert _storage_uri() == "redis://dedicated:6379"
