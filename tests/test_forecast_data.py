"""Hermetic tests for model loading in ``processing/forecast_data``.

``load_regression_model`` is the forecast-side counterpart of the model save/load
path, so it also guards the LightGBM ``NotFittedError`` regression: a saved model
must be reloadable and able to predict. ``MODELS_PATH`` is monkeypatched to a temp
dir so nothing touches the real models tree, and a NullCache app context satisfies
the ``@cache.memoize`` decorator.
"""

from json import dumps

import numpy as np
import pytest
from flask import Flask
from pandas import date_range, DataFrame

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a ``processing`` submodule first hits a circular import.
import api.config  # noqa: F401
from api.config.cache import cache
from models import make_model
from processing import forecast_data


@pytest.fixture
def app_context():
    app = Flask(__name__)
    cache.init_app(app, {"CACHE_TYPE": "NullCache"})
    with app.app_context():
        yield


def test_load_regression_model_roundtrips_lightgbm(app_context, tmp_path, monkeypatch):
    # Regression for the LightGBM save/load bug: the reloaded model must predict
    # without raising NotFittedError.
    monkeypatch.setattr(forecast_data, "MODELS_PATH", tmp_path)
    model_dir = tmp_path / "skopje" / "1000" / "pm2_5"
    model_dir.mkdir(parents=True)

    rng = np.random.RandomState(0)
    x = rng.rand(100, 3)
    y = x @ np.array([1.0, 2.0, -1.0])
    model = make_model("LightGBMRegressionModel")
    model.set_params(verbose=-1)
    model.train(x, y)
    model.save(model_dir)
    (model_dir / "selected_features.json").write_text(dumps(["a", "b", "c"]))

    result = forecast_data.load_regression_model("skopje", "1000", "pm2_5")
    assert result is not None
    loaded_model, features = result
    assert features == ["a", "b", "c"]
    predictions = loaded_model.predict(x)  # must not raise NotFittedError
    assert len(predictions) == len(y)


def test_load_regression_model_missing_returns_none(app_context, tmp_path, monkeypatch):
    monkeypatch.setattr(forecast_data, "MODELS_PATH", tmp_path)
    assert forecast_data.load_regression_model("nope", "nope", "pm2_5") is None


def test_recursive_forecast_logs_each_step_it_could_not_predict(
    app_context, tmp_path, monkeypatch, caplog
):
    """A step that fails yields NaN, and now says so.

    The handler around the per-step prediction stays deliberately broad: each hour is
    forecast from the hour before it, so abandoning the loop on the first failure would
    throw away the rest of the horizon too, and NaN is already how this function reports
    "no value for this hour".

    What it lacked was any record. A model that failed on every single step returned an
    all-NaN series, which reads exactly like a sensor with nothing to forecast -- so a
    broken model stayed invisible for as long as nobody compared it against a working one.
    """
    frame = DataFrame(
        {"pm2_5": [10.0, 11.0, 12.0]},
        index=date_range("2026-01-01", periods=3, freq="1h"),
    )
    monkeypatch.setattr(
        forecast_data, "fetch_summary_dataframe", lambda *args, **kwargs: frame
    )
    monkeypatch.setattr(forecast_data, "DATA_PROCESSED_PATH", tmp_path)

    def unavailable(*args, **kwargs):
        raise RuntimeError("upstream feature service is down")

    monkeypatch.setattr(forecast_data, "forecast_sensor", unavailable)

    with caplog.at_level("ERROR", logger=forecast_data.__name__):
        result = forecast_data.recursive_forecast(
            "skopje", "1000", "pm2_5", model=None, model_features=[], n_steps=3
        )

    # Still a full-length series of NaN: the loop runs to the end of the horizon.
    assert len(result.index) == 2
    assert bool(result.isnull().all())
    # One record per failed step, each naming the sensor and the hour, and each carrying
    # the original traceback rather than just the fact that something went wrong.
    assert len(caplog.records) == 3
    assert all("skopje" in record.message for record in caplog.records)
    assert all("1000" in record.message for record in caplog.records)
    assert all(record.exc_info is not None for record in caplog.records)
