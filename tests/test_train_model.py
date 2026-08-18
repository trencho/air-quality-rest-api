"""Hermetic unit tests for the pure helpers in ``modeling/train_model``.

The training orchestration itself (hyper-parameter search, model persistence, plots)
is not exercised here — only the small, I/O-free frame transform it relies on.
"""

import pytest
from pandas import DataFrame, date_range

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a package submodule first can hit a circular import.
import api.config  # noqa: F401
from modeling.train_model import previous_value_overwrite
from utils import BatchOutcome


def test_previous_value_overwrite_shifts_up_and_drops_last_row():
    # Each row takes the next row's values (shift up by one); the trailing NaN row
    # that leaves is dropped, so an n-row frame becomes n-1 rows.
    dataframe = DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    result = previous_value_overwrite(dataframe)
    assert result.to_dict("list") == {"a": [2.0, 3.0], "b": [5.0, 6.0]}
    assert len(result.index) == 2


# --- train_regression_model's outcome, which is what the model_training tally counts ---


@pytest.fixture
def training_stubs(monkeypatch, tmp_path):
    """Neuter everything training does to disk, leaving only the outcome decision."""
    from modeling import train_model

    monkeypatch.setattr(train_model, "MODELS_PATH", tmp_path / "models")
    monkeypatch.setattr(train_model, "DATA_PROCESSED_PATH", tmp_path / "processed")
    monkeypatch.setattr(train_model, "check_best_regression_model", lambda path: False)
    monkeypatch.setattr(train_model, "check_pollutant_lock", lambda path: False)
    monkeypatch.setattr(train_model, "create_pollutant_lock", lambda path: None)
    monkeypatch.setattr(train_model, "remove_pollutant_lock", lambda path: None)
    monkeypatch.setattr(train_model, "draw_errors", lambda *args: None)
    monkeypatch.setattr(train_model, "draw_predictions", lambda *args: None)
    trained = []
    monkeypatch.setattr(
        train_model,
        "generate_regression_model",
        lambda frame, city, sensor, pollutant: trained.append(pollutant),
    )
    return train_model, trained


_CITY = {"cityName": "skopje"}
_SENSOR = {"sensorId": "1000"}


def _frame_with(columns):
    index = date_range("2026-01-01", periods=3, freq="1h")
    return DataFrame({column: [1.0, 2.0, 3.0] for column in columns}, index=index)


def test_train_regression_model_reports_done_when_it_trained(
    training_stubs, monkeypatch
):
    train_model, trained = training_stubs
    monkeypatch.setattr(
        train_model, "fetch_summary_dataframe", lambda *a, **k: _frame_with(["pm2_5"])
    )

    outcome = train_model.train_regression_model(_CITY, _SENSOR, "pm2_5")

    assert trained == ["pm2_5"]
    assert outcome is BatchOutcome.DONE


def test_train_regression_model_reports_skipped_when_the_sensor_lacks_the_pollutant(
    training_stubs, monkeypatch
):
    # The distinction the model_training tally exists for. This path used to log
    # "Completed training model" and return None, so a run in which not one sensor
    # reported the pollutant was indistinguishable from a run that trained every model.
    train_model, trained = training_stubs
    monkeypatch.setattr(
        train_model, "fetch_summary_dataframe", lambda *a, **k: _frame_with(["no2"])
    )

    outcome = train_model.train_regression_model(_CITY, _SENSOR, "pm2_5")

    assert trained == [], "nothing should be trained without the pollutant column"
    assert outcome is BatchOutcome.SKIPPED


def test_train_regression_model_reports_skipped_when_a_model_already_exists(
    training_stubs, monkeypatch
):
    train_model, _ = training_stubs
    monkeypatch.setattr(train_model, "check_best_regression_model", lambda path: True)

    assert (
        train_model.train_regression_model(_CITY, _SENSOR, "pm2_5")
        is BatchOutcome.SKIPPED
    )


def test_train_regression_model_reports_failed_when_training_raises(
    training_stubs, monkeypatch
):
    train_model, _ = training_stubs
    monkeypatch.setattr(
        train_model, "fetch_summary_dataframe", lambda *a, **k: _frame_with(["pm2_5"])
    )

    def explode(*args):
        raise RuntimeError("the model would not fit")

    monkeypatch.setattr(train_model, "generate_regression_model", explode)

    assert (
        train_model.train_regression_model(_CITY, _SENSOR, "pm2_5")
        is BatchOutcome.FAILED
    )
