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
