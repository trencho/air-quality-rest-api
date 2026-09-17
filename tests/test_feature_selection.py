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


def test_constant_features_are_never_selected(features):
    """A zero-variance column carries no information and must not survive elimination.

    Before 2026-09-17 it always did, and in numbers. A block of time features
    (``month_*``, ``quarter_*``, ``season_*``, ``isLeapYear`` and friends) is constant
    across any training window shorter than the period it encodes, and those columns are
    mutually proportional. Fifteen of them collapse that block of the design matrix to
    rank 1, statsmodels falls back to a pseudo-inverse, and every collinear column comes
    back with ``p ~ 0`` -- reading as perfectly significant. Measured on the real training
    calls: 27 features in and all 12 constants kept, 37 in and all 14 kept.
    """
    x = DataFrame(
        {
            "signal": features["signal"],
            "month_cos": np.ones(200),
            "quarter_sin": np.zeros(200),
            "isLeapYear": np.ones(200),
        }
    )
    y = Series(2 * features["signal"] + 0.01 * features["eps"])
    assert backward_elimination(x, y) == ["signal"]


def test_constant_features_do_not_evict_informative_ones(features):
    """The harm is not the useless columns, it is what they push out.

    Scoring ``p ~ 0``, the constants are never the argmax, so the loop removes real
    features instead to make progress. One measured call dropped 16 informative features
    while retaining all 14 constants.
    """
    x = DataFrame(
        {
            "a": features["signal"],
            "b": features["noise"],
            "const_1": np.ones(200),
            "const_2": np.full(200, 7.0),
            "const_3": np.zeros(200),
        }
    )
    y = Series(2 * features["signal"] + 3 * features["noise"] + 0.01 * features["eps"])
    assert sorted(backward_elimination(x, y)) == ["a", "b"]


def test_p_values_are_selected_by_name_not_position(features):
    """``pvalues[1:]`` assumed an intercept that is always present and always first.

    That holds only while ``has_constant="add"`` forces one in, which is the argument that
    manufactures the collinearity above. Selecting by name holds either way, and is what
    lets the argument be corrected.
    """
    x = DataFrame({"signal": features["signal"], "noise": features["noise"]})
    y = Series(2 * features["signal"] + 0.01 * features["eps"])
    p_values = get_p_values(x, y, ["noise", "signal"])
    assert list(p_values.index) == ["noise", "signal"]
    assert p_values["signal"] < 0.05
    assert "const" not in p_values.index
