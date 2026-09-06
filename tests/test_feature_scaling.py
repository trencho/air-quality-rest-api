"""Unit tests for the two halves of ``processing/feature_scaling``."""

import pytest
from pandas import DataFrame

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a ``processing`` submodule first hits a circular import.
import api.config  # noqa: F401
from processing.feature_scaling import apply_scaler, fit_scaler


def test_fit_scaler_min_max():
    result, scaler = fit_scaler(DataFrame({"a": [0.0, 5.0, 10.0]}), scale="min_max")
    assert result["a"].tolist() == pytest.approx([0.0, 0.5, 1.0])
    assert list(result.columns) == ["a"]
    assert scaler is not None


def test_fit_scaler_preserves_index_and_columns():
    frame = DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]}, index=[10, 20, 30])
    result, _ = fit_scaler(frame)  # default RobustScaler
    assert list(result.columns) == ["a", "b"]
    assert result.index.tolist() == [10, 20, 30]
    assert result.shape == (3, 2)


def test_each_fit_gets_its_own_scaler_instance():
    """The three scalers used to be module-level INSTANCES in a dict, shared by every caller.

    Training spawns a thread per (city, sensor, pollutant) and `fit_transform` mutates the scaler,
    so a shared instance is a race waiting for the first caller that names a scaler. Nothing named
    one in production, which is why this was a trap rather than a live bug.
    """
    _, first = fit_scaler(DataFrame({"a": [0.0, 1.0]}), scale="min_max")
    _, second = fit_scaler(DataFrame({"a": [0.0, 100.0]}), scale="min_max")
    assert first is not second


def test_apply_scaler_reuses_the_training_statistics():
    """The point of persisting a scaler: the same input maps to the same number later."""
    train = DataFrame({"a": [0.0, 10.0]})
    scaled_train, scaler = fit_scaler(train, scale="min_max")
    assert scaled_train["a"].tolist() == pytest.approx([0.0, 1.0])

    # Fitted on 0..10, so 5.0 is 0.5 -- and 20.0 is 2.0, ABOVE the training range. Refitting
    # would map 20.0 back to 1.0 and silently rescale the whole frame.
    later = apply_scaler(DataFrame({"a": [5.0, 20.0]}), scaler)
    assert later["a"].tolist() == pytest.approx([0.5, 2.0])


def test_apply_scaler_does_not_fit():
    """A scaler with no `fit` proves it by construction."""

    class TransformOnly:
        def transform(self, frame):
            return frame * 0 + 7

    result = apply_scaler(DataFrame({"a": [1.0, 2.0]}), TransformOnly())
    assert result["a"].tolist() == [7.0, 7.0]
