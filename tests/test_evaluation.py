"""Hermetic tests for the forecast-quality (evaluation) blueprint.

Seeds a best-model ``.mdl`` plus its ``error.csv`` under temp MODELS/RESULTS trees and
exercises the handlers directly (tiny Flask + NullCache app context), with the location
lookups patched — the ``test_missing_data.py`` pattern.
"""

from unittest.mock import patch

import pytest
from flask import Flask, Response

# Import the config package first so the api.blueprints chain initialises in order.
import api.config  # noqa: F401
from api.blueprints.evaluation import evaluation
from api.config.cache import cache
from api.config.converters import PollutantType

_MOD = "api.blueprints.evaluation.evaluation"
_HEADER = (
    "Mean Absolute Error,Mean Absolute Percentage Error,"
    "Mean Squared Error,Root Mean Squared Error"
)


@pytest.fixture
def app_context():
    app = Flask(__name__)
    cache.init_app(app, {"CACHE_TYPE": "NullCache"})
    with app.app_context():
        yield


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    models_path = tmp_path / "models"
    errors_path = tmp_path / "results" / "errors"
    monkeypatch.setattr(evaluation, "MODELS_PATH", models_path)
    monkeypatch.setattr(evaluation, "RESULTS_ERRORS_PATH", errors_path)
    return models_path, errors_path


def _seed(paths, city, sensor, pollutant, model, row):
    models_path, errors_path = paths
    pollutant_dir = models_path / city / sensor / pollutant
    pollutant_dir.mkdir(parents=True, exist_ok=True)
    (pollutant_dir / f"{model}.mdl").write_bytes(b"model")
    error_dir = errors_path / "data" / city / sensor / pollutant / model
    error_dir.mkdir(parents=True, exist_ok=True)
    (error_dir / "error.csv").write_text(f"{_HEADER}\n{row}\n")


def test_read_best_model_evaluation_returns_metrics(seeded):
    _seed(
        seeded, "skopje", "1000", "pm2_5", "LightGBMRegressionModel", "1.5,10.0,4.0,2.0"
    )
    result = evaluation._read_best_model_evaluation("skopje", "1000", "pm2_5")
    assert result["model"] == "LightGBMRegressionModel"
    assert result["metrics"]["Mean Absolute Error"] == 1.5
    assert result["metrics"]["Root Mean Squared Error"] == 2.0


def test_read_best_model_evaluation_no_model_returns_none(seeded):
    assert evaluation._read_best_model_evaluation("nowhere", "0", "pm2_5") is None


def test_pollutant_evaluation_unknown_city_returns_404(app_context, seeded):
    with patch(f"{_MOD}.check_city", return_value=None):
        result = evaluation.fetch_pollutant_evaluation(
            "nowhere", "1", PollutantType.PM2_5
        )
    assert isinstance(result, tuple) and result[1] == 404


def test_pollutant_evaluation_no_model_returns_404(app_context, seeded):
    with patch(f"{_MOD}.check_city", return_value={"cityName": "skopje"}), patch(
        f"{_MOD}.check_sensor", return_value={"sensorId": "1000"}
    ):
        result = evaluation.fetch_pollutant_evaluation(
            "skopje", "1000", PollutantType.PM2_5
        )
    assert isinstance(result, tuple) and result[1] == 404


def test_pollutant_evaluation_returns_metrics(app_context, seeded):
    _seed(seeded, "skopje", "1000", "pm2_5", "XGBoostRegressionModel", "2.0,,9.0,3.0")
    with patch(f"{_MOD}.check_city", return_value={"cityName": "skopje"}), patch(
        f"{_MOD}.check_sensor", return_value={"sensorId": "1000"}
    ):
        response = evaluation.fetch_pollutant_evaluation(
            "skopje", "1000", PollutantType.PM2_5
        )
    assert isinstance(response, Response)
    body = response.get_json()
    assert body["model"] == "XGBoostRegressionModel"
    assert body["metrics"]["Mean Absolute Error"] == 2.0
    assert body["metrics"]["Mean Absolute Percentage Error"] is None  # empty -> None


def test_sensor_evaluation_aggregates_pollutants(app_context, seeded):
    _seed(
        seeded, "skopje", "1000", "pm2_5", "LightGBMRegressionModel", "1.5,10.0,4.0,2.0"
    )
    _seed(
        seeded,
        "skopje",
        "1000",
        "no2",
        "RandomForestRegressionModel",
        "0.5,5.0,1.0,1.0",
    )
    with patch(f"{_MOD}.check_city", return_value={"cityName": "skopje"}), patch(
        f"{_MOD}.check_sensor", return_value={"sensorId": "1000"}
    ):
        response = evaluation.fetch_sensor_evaluation("skopje", "1000")
    body = response.get_json()
    assert set(body) == {"pm2_5", "no2"}
    assert body["no2"]["model"] == "RandomForestRegressionModel"
