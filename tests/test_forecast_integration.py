"""Integration tests for the forecast computation path (``processing/forecast_data``).

Unlike the unit tests, these wire the whole pipeline together with real seeded
artifacts under a temp tree: a trained-and-saved model plus processed weather/pollution
CSVs. ``forecast_city_sensor`` then exercises model loading -> two-CSV summary read ->
the 24-step recursive forecast loop -> feature generation/scaling -> prediction, and
``fetch_forecast_result`` aggregates the per-pollutant series into the timestamp dict.

The model is trained on time-derived features (hour/month cyclic encodings), which are
defined for future steps from the datetime index alone — so the recursion yields real
predictions without needing future weather rows (which a static fixture can't provide).
"""

from json import dumps

import numpy as np
import pytest
from flask import Flask
from pandas import DataFrame, DatetimeIndex, Series, Timedelta, date_range

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a ``processing`` submodule first hits a circular import.
import api.config  # noqa: F401
from api.config.cache import cache
from models import make_model
from processing import forecast_data
from processing.feature_generation import generate_features
from processing.normalize_data import current_hour

_TIME_FEATURES = ["hour_cos", "hour_sin", "month_cos", "month_sin"]


@pytest.fixture
def app_context():
    app = Flask(__name__)
    cache.init_app(app, {"CACHE_TYPE": "NullCache"})
    with app.app_context():
        yield


@pytest.fixture
def forecast_env(tmp_path, monkeypatch):
    """Seed processed CSVs + a saved model for skopje/1000/pm2_5 and point
    forecast_data at the temp tree."""
    processed = tmp_path / "processed"
    models_path = tmp_path / "models"
    sensor_dir = processed / "skopje" / "1000"
    sensor_dir.mkdir(parents=True)
    model_dir = models_path / "skopje" / "1000" / "pm2_5"
    model_dir.mkdir(parents=True)

    n = 400
    index = date_range(end=current_hour(), periods=n, freq="h")
    seconds = (index.astype("int64") // 10**9).astype("int64")
    rng = np.random.RandomState(1)
    temperature = 10 + 5 * rng.rand(n)
    # Positive, hourly-seasonal target so predictions stay in a sane, positive range.
    pm2_5 = 20 + 5 * np.sin(np.arange(n) * 2 * np.pi / 24) + rng.rand(n)
    DataFrame({"time": seconds, "temp": temperature}).to_csv(
        sensor_dir / "weather.csv", index=False
    )
    DataFrame({"time": seconds, "pm2_5": pm2_5, "pm10": pm2_5 * 1.5}).to_csv(
        sensor_dir / "pollution.csv", index=False
    )

    target = Series(pm2_5, index=index)
    features = generate_features(target, 25)[_TIME_FEATURES].dropna()
    model = make_model("LinearRegressionModel")
    model.train(features, target.loc[features.index])
    model.save(model_dir)
    (model_dir / "selected_features.json").write_text(dumps(_TIME_FEATURES))

    monkeypatch.setattr(forecast_data, "DATA_PROCESSED_PATH", processed)
    monkeypatch.setattr(forecast_data, "MODELS_PATH", models_path)
    return processed, models_path


def test_forecast_city_sensor_produces_finite_forecast(app_context, forecast_env):
    result = forecast_data.forecast_city_sensor("skopje", "1000", "pm2_5")

    assert isinstance(result, Series)
    assert len(result) == 24  # 25 horizon steps minus the dropped first
    assert isinstance(result.index, DatetimeIndex)
    assert result.index[1] - result.index[0] == Timedelta(hours=1)
    # Real predictions flowed through the pipeline (not the all-NaN degenerate path),
    # and they land in the trained target's positive range.
    assert result.notna().any()
    assert (result.dropna() > 0).all()


def test_forecast_city_sensor_without_model_returns_none(app_context, forecast_env):
    # No model was saved for "co", so there is nothing to forecast with.
    assert forecast_data.forecast_city_sensor("skopje", "1000", "co") is None


def test_fetch_forecast_result_aggregates_by_timestamp(app_context, forecast_env):
    result = forecast_data.fetch_forecast_result(
        {"cityName": "skopje", "countryCode": "MK"}, {"sensorId": "1000"}
    )

    assert len(result) == 24
    entry = result[sorted(result)[0]]
    assert {"dateTime", "time", "pm2_5"} <= set(entry)
    assert entry["pm2_5"] is not None
