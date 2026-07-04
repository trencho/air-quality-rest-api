"""Hermetic unit tests for ``value_scaling`` in ``processing/feature_scaling``."""

import pytest
from pandas import DataFrame

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a ``processing`` submodule first hits a circular import.
import api.config  # noqa: F401
from processing.feature_scaling import value_scaling


def test_value_scaling_min_max():
    result = value_scaling(DataFrame({"a": [0.0, 5.0, 10.0]}), scale="min_max")
    assert result["a"].tolist() == pytest.approx([0.0, 0.5, 1.0])
    assert list(result.columns) == ["a"]


def test_value_scaling_preserves_index_and_columns():
    frame = DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]}, index=[10, 20, 30])
    result = value_scaling(frame)  # default RobustScaler
    assert list(result.columns) == ["a", "b"]
    assert result.index.tolist() == [10, 20, 30]
    assert result.shape == (3, 2)
