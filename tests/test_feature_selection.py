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
from processing.feature_selection import (
    backward_elimination,
    estimable_features,
    get_p_values,
)


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


def test_nested_indicators_collapse_to_one(features):
    """``isYearStart`` implies ``isQuarterStart`` implies ``isMonthStart``.

    Over a window containing no month-start except 1 January the three are the *same column*.
    Found 2026-09-17 by taking the SVD of a real design matrix: rank 1 of 3, which was exactly
    the residual rank deficiency of 2 left after constant columns were excluded. Only the
    first survives, and elimination then judges it on its merits.
    """
    same = np.zeros(200)
    same[:23] = 1.0
    x = DataFrame(
        {
            "signal": features["signal"],
            "isMonthStart": same,
            "isQuarterStart": same.copy(),
            "isYearStart": same.copy(),
        }
    )
    assert estimable_features(x) == ["signal", "isMonthStart"]


def test_an_exact_linear_combination_is_dropped(features):
    """``c = a + b`` has no unique coefficient, and elimination keeps all three without this."""
    x = DataFrame(
        {
            "a": features["signal"],
            "b": features["noise"],
            "c": features["signal"] + features["noise"],
        }
    )
    assert estimable_features(x) == ["a", "b"]


def test_merely_correlated_features_are_both_kept(features):
    """The guard against over-correcting, and the reason columns are scaled first.

    ``matrix_rank`` takes its tolerance from the largest singular value, so on a frame mixing
    pollutant lags with cyclic encodings in [-1, 1] an unscaled test can call a
    small-magnitude column dependent purely for being small. These two correlate at ~0.999
    and are genuinely distinct; dropping either would be a regression.
    """
    near = features["signal"] + 1e-3 * features["eps"]
    x = DataFrame({"signal": features["signal"], "near": near})
    assert estimable_features(x) == ["signal", "near"]

    scaled = DataFrame(
        {"big": features["signal"] * 1e6, "small": features["noise"] * 1e-6}
    )
    assert estimable_features(scaled) == ["big", "small"]
