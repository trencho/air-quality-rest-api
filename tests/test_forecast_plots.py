"""Hermetic tests for the forecast and plots blueprints (no network, no ML data).

These two blueprints had no coverage. Rather than add network-bound endpoint tests,
this exercises the handlers directly under a tiny ``Flask`` + ``NullCache`` app context
and patches the location lookups (the pattern from ``test_missing_data.py``), covering:

* the 404 guards — unknown city / sensor / far-away coordinates / missing plot image, and
* ``return_sensor_forecast_results``' empty-data fallback when neither a processed
  ``predictions.json`` nor a stored prediction exists.
"""

from unittest.mock import patch

import pytest
from flask import Flask, Response

# Initialise the config package before pulling names out of ``api.blueprints`` so the
# package initialises first (importing ``api.blueprints`` first is a circular import).
import api.config  # noqa: F401
from api.blueprints.forecast.forecast import (
    fetch_city_coordinates_forecast,
    fetch_city_forecast,
    fetch_sensor_coordinates_forecast,
    fetch_sensor_forecast,
    return_sensor_forecast_results,
)
from api.blueprints.plots.plots import fetch_plots_errors, fetch_plots_predictions
from api.config.cache import cache
from api.config.converters import ErrorType, PollutantType

_FORECAST = "api.blueprints.forecast.forecast"
_PLOTS = "api.blueprints.plots.plots"


@pytest.fixture
def app_context():
    app = Flask(__name__)
    cache.init_app(app, {"CACHE_TYPE": "NullCache"})
    with app.app_context():
        yield


def _assert_404(result) -> None:
    assert isinstance(
        result, tuple
    ), f"expected a (Response, status) tuple, got {result!r}"
    response, status = result
    assert status == 404
    assert isinstance(response, Response)


# --- forecast --------------------------------------------------------------


def test_city_forecast_unknown_city_returns_404(app_context):
    with patch(f"{_FORECAST}.check_city", return_value=None):
        _assert_404(fetch_city_forecast("nowhere"))


def test_city_coordinates_forecast_far_away_returns_404(app_context):
    with patch(f"{_FORECAST}.calculate_nearest_city", return_value=None):
        _assert_404(fetch_city_coordinates_forecast(0.0, 0.0))


def test_sensor_forecast_unknown_city_returns_404(app_context):
    with patch(f"{_FORECAST}.check_city", return_value=None):
        _assert_404(fetch_sensor_forecast("nowhere", "1"))


def test_sensor_forecast_unknown_sensor_returns_404(app_context):
    with patch(f"{_FORECAST}.check_city", return_value={"cityName": "skopje"}), patch(
        f"{_FORECAST}.check_sensor", return_value=None
    ):
        _assert_404(fetch_sensor_forecast("skopje", "9999"))


def test_sensor_coordinates_forecast_far_away_returns_404(app_context):
    with patch(f"{_FORECAST}.calculate_nearest_sensor", return_value=None):
        _assert_404(fetch_sensor_coordinates_forecast(0.0, 0.0))


def test_return_sensor_forecast_results_no_data_is_empty(app_context):
    # No processed predictions.json and an empty repository → the helper falls through
    # to an empty ``data`` list while still echoing the sensor's coordinates.
    city = {
        "cityName": "no-city",
        "countryCode": "MK",
        "cityLocation": {"latitude": "42.0", "longitute": "21.4"},
    }
    sensor = {"sensorId": "no-sensor", "position": "42.0,21.4"}
    forecast = return_sensor_forecast_results(city, sensor)
    assert forecast["data"] == []
    assert forecast["latitude"] == 42.0
    assert forecast["longitude"] == 21.4


# --- plots -----------------------------------------------------------------


def test_plots_predictions_unknown_city_returns_404(app_context):
    with patch(f"{_PLOTS}.check_city", return_value=None):
        _assert_404(fetch_plots_predictions("nowhere", "1", PollutantType.PM2_5))


def test_plots_predictions_unknown_sensor_returns_404(app_context):
    with patch(f"{_PLOTS}.check_city", return_value={"cityName": "skopje"}), patch(
        f"{_PLOTS}.check_sensor", return_value=None
    ):
        _assert_404(fetch_plots_predictions("skopje", "9999", PollutantType.PM2_5))


def test_plots_predictions_missing_image_returns_404(app_context):
    # Both lookups pass but no rendered PNG exists for this (bogus) city/sensor.
    with patch(f"{_PLOTS}.check_city", return_value={"cityName": "no-city"}), patch(
        f"{_PLOTS}.check_sensor", return_value={"sensorId": "no-sensor"}
    ):
        _assert_404(
            fetch_plots_predictions("no-city", "no-sensor", PollutantType.PM2_5)
        )


def test_plots_errors_unknown_city_returns_404(app_context):
    with patch(f"{_PLOTS}.check_city", return_value=None):
        _assert_404(
            fetch_plots_errors(
                "nowhere", "1", PollutantType.PM2_5, ErrorType.MEAN_ABSOLUTE_ERROR
            )
        )


def test_plots_errors_missing_image_returns_404(app_context):
    with patch(f"{_PLOTS}.check_city", return_value={"cityName": "no-city"}), patch(
        f"{_PLOTS}.check_sensor", return_value={"sensorId": "no-sensor"}
    ):
        _assert_404(
            fetch_plots_errors(
                "no-city",
                "no-sensor",
                PollutantType.PM2_5,
                ErrorType.MEAN_ABSOLUTE_ERROR,
            )
        )
