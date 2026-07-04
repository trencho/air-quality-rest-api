"""Hermetic tests for the error handlers (``api.blueprints.errors``).

Guards a real bug the rate-limit integration exposed: the catch-all ``Exception``
handler masked every ``HTTPException`` (429, 405, ...) as a 500. HTTP errors must keep
their status; only unexpected non-HTTP exceptions become 500.
"""

from json import loads

import pytest
from flask import Flask, abort

# Import the config package first so the api.blueprints chain initialises in order.
import api.config  # noqa: F401
from api.blueprints.errors import errors_blueprint


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(errors_blueprint)

    @app.route("/method-not-allowed")
    def _method_not_allowed():
        abort(405)

    @app.route("/boom")
    def _boom():
        raise ValueError("kaboom")

    return app.test_client()


def test_http_exception_keeps_its_status(client):
    response = client.get("/method-not-allowed")
    assert response.status_code == 405
    assert loads(response.data)["error_message"]  # JSON body, not a 500


def test_unexpected_exception_is_500(client):
    response = client.get("/boom")
    assert response.status_code == 500
    assert loads(response.data)["error_message"] == "Unhandled exception"


def test_unknown_route_is_404(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert loads(response.data)["error_message"] == "Resource not found"
