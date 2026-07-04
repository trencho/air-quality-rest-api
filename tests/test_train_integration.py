"""Integration test for the model-training path (``modeling/train_model``).

Wires ``generate_regression_model`` end-to-end over a seeded time series: feature
generation -> split + backward elimination -> train each candidate model -> predict
-> save per-model results/errors -> pick the best -> persist the best model and its
selected features. Module paths are redirected to a temp tree so nothing touches the
real models/results dirs.

Two knobs keep it fast and deterministic without changing the orchestration under test:
``hyper_parameter_tuning`` is stubbed to skip the RandomizedSearchCV (that's sklearn's
search, not app logic), and ``REGRESSION_MODELS`` is set to two plain sklearn models so
best-model selection runs without native-library non-determinism.
"""

from json import loads

import numpy as np
import pytest
from pandas import DataFrame, date_range

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a package submodule first can hit a circular import.
import api.config  # noqa: F401
from models import make_model
from modeling import process_results, train_model
from processing.normalize_data import current_hour

_MODELS = {
    "LinearRegressionModel": "Linear",
    "DecisionTreeRegressionModel": "Decision Tree",
}


@pytest.fixture
def train_env(tmp_path, monkeypatch):
    models_path = tmp_path / "models"
    errors_path = tmp_path / "results" / "errors"
    predictions_path = tmp_path / "results" / "predictions"
    for path in (models_path, errors_path, predictions_path):
        path.mkdir(parents=True)

    monkeypatch.setattr(train_model, "MODELS_PATH", models_path)
    monkeypatch.setattr(train_model, "RESULTS_ERRORS_PATH", errors_path)
    monkeypatch.setattr(train_model, "RESULTS_PREDICTIONS_PATH", predictions_path)
    monkeypatch.setattr(process_results, "RESULTS_ERRORS_PATH", errors_path)
    monkeypatch.setattr(process_results, "RESULTS_PREDICTIONS_PATH", predictions_path)
    monkeypatch.setattr(
        train_model, "hyper_parameter_tuning", lambda model, x, y, path: {}
    )
    monkeypatch.setattr(train_model, "REGRESSION_MODELS", _MODELS)

    n = 400
    index = date_range(end=current_hour(), periods=n, freq="h")
    rng = np.random.RandomState(2)
    dataframe = DataFrame(
        {
            "pm2_5": 20 + 5 * np.sin(np.arange(n) * 2 * np.pi / 24) + rng.rand(n),
            "pm10": 30 + rng.rand(n),
            "temp": 10 + 5 * rng.rand(n),
        },
        index=index,
    )
    return dataframe, models_path, errors_path, predictions_path


def test_generate_regression_model_trains_evaluates_and_saves_best(train_env):
    dataframe, models_path, errors_path, predictions_path = train_env

    train_model.generate_regression_model(dataframe, "skopje", "1000", "pm2_5")

    pollutant_dir = models_path / "skopje" / "1000" / "pm2_5"

    # Exactly one best model is persisted at the pollutant level (glob is non-recursive,
    # so it doesn't match the per-model subdirs' files).
    best_models = list(pollutant_dir.glob("*.mdl"))
    assert len(best_models) == 1
    assert best_models[0].stem in _MODELS

    # Selected features saved as a non-empty list.
    selected = loads((pollutant_dir / "selected_features.json").read_text())
    assert isinstance(selected, list) and selected

    # Every candidate model produced evaluation artifacts.
    assert {f.parent.name for f in errors_path.rglob("error.csv")} == set(_MODELS)
    assert {f.parent.name for f in predictions_path.rglob("prediction.csv")} == set(
        _MODELS
    )

    # The persisted best model reloads and predicts on the selected-feature shape.
    best = make_model(best_models[0].stem)
    best.load(pollutant_dir)
    predictions = best.predict(np.zeros((1, len(selected))))
    assert len(predictions) == 1
