"""Hermetic tests for the Prometheus /metrics endpoint (``api.config.metrics``)."""

import pytest
from flask import Flask

# Import the config package first so the api chain initialises in order.
import api.config  # noqa: F401
from api.config.limiter import init_limiter, limiter
from api.config.metrics import init_metrics
from definitions import METRICS_PATH


@pytest.fixture
def app():
    app = Flask(__name__)

    @app.route("/hello")
    def _hello():
        return "hi"

    init_metrics(app)
    return app


def test_metrics_endpoint_exposes_prometheus_format(app):
    response = app.test_client().get(METRICS_PATH)
    assert response.status_code == 200
    assert "text/plain" in response.headers["Content-Type"]
    assert b"flask_http_request_total" in response.data


def test_metrics_endpoint_records_requests(app):
    client = app.test_client()
    client.get("/hello")
    client.get("/hello")
    body = client.get(METRICS_PATH).data
    # The request counter is exported for the instrumented endpoint.
    assert b"flask_http_request_total" in body


def test_metrics_endpoint_is_exempt_from_rate_limit():
    # Even with the limiter active and the default 60/minute limit, the scrape
    # endpoint must never be throttled (Prometheus polls it frequently).
    limiter.enabled = True
    try:
        app = Flask(__name__)
        init_limiter(app)
        init_metrics(app)
        limiter.reset()
        client = app.test_client()
        statuses = {client.get(METRICS_PATH).status_code for _ in range(62)}
        assert statuses == {200}
    finally:
        limiter.reset()
        limiter.enabled = False
