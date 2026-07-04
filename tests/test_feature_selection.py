"""Hermetic unit tests for backward feature elimination (``processing/feature_selection``).

Uses a fixed synthetic dataset: one strongly predictive feature and one pure-noise
feature, so elimination has a deterministic outcome (the noise column is dropped).
"""

import numpy as np
import pytest
from pandas import DataFrame, Series

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a ``processing`` submodule first hits a circular import.
import api.config  # noqa: F401
from processing.feature_selection import backward_elimination, get_p_values


@pytest.fixture(scope="module")
def features() -> dict:
    rng = np.random.RandomState(0)
    return {"signal": rng.rand(200), "noise": rng.rand(200), "eps": rng.rand(200)}


def test_backward_elimination_drops_insignificant_feature(features):
    x = DataFrame({"signal": features["signal"], "noise": features["noise"]})
    y = Series(2 * features["signal"] + 0.01 * features["eps"])
    assert backward_elimination(x, y) == ["signal"]


def test_backward_elimination_keeps_all_significant(features):
    x = DataFrame({"a": features["signal"], "b": features["noise"]})
    y = Series(2 * features["signal"] + 3 * features["noise"] + 0.01 * features["eps"])
    assert sorted(backward_elimination(x, y)) == ["a", "b"]


def test_get_p_values_indexed_by_features(features):
    x = DataFrame({"signal": features["signal"], "noise": features["noise"]})
    y = Series(2 * features["signal"] + 0.01 * features["eps"])
    p_values = get_p_values(x, y, ["signal", "noise"])
    assert list(p_values.index) == ["signal", "noise"]
    assert p_values["signal"] < 0.05
    assert p_values["noise"] > 0.05
