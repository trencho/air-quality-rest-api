"""Hermetic unit tests for the pure helpers in ``processing/feature_generation``.

Covers season lookup, cyclic/categorical encoding, and a ``generate_time_features``
smoke test. The heavier lag/pacf path (``generate_lag_features``) isn't covered here.
"""

from datetime import datetime

import pytest
from pandas import DataFrame, Series, date_range

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a ``processing`` submodule first hits a circular import.
import api.config  # noqa: F401
from processing.feature_generation import (
    encode_categorical_data,
    encode_cyclic_data,
    generate_time_features,
    get_season,
)


@pytest.mark.parametrize(
    "month, day, expected",
    [
        (1, 15, "winter"),
        (4, 15, "spring"),
        (7, 15, "summer"),
        (10, 15, "autumn"),
        (12, 25, "winter"),  # late December wraps back to winter
    ],
)
def test_get_season(month, day, expected):
    assert get_season(datetime(2024, month, day)) == expected


def test_encode_cyclic_data_adds_cos_and_sin():
    features = DataFrame(index=[0, 1])
    encode_cyclic_data(features, "hour", Series([0, 6]), 24)
    assert list(features.columns) == ["hour_cos", "hour_sin"]
    assert features["hour_cos"].tolist() == pytest.approx([1.0, 0.0], abs=1e-9)
    assert features["hour_sin"].tolist() == pytest.approx([0.0, 1.0], abs=1e-9)


def test_encode_categorical_data_maps_to_codes():
    dataframe = DataFrame({"c": ["x", "y", "x"]})
    encode_categorical_data(dataframe)
    assert dataframe["c"].tolist() == [0, 1, 0]


def test_generate_time_features_shape_and_index():
    target = Series(range(48), index=date_range("2024-01-01", periods=48, freq="h"))
    features = generate_time_features(target)
    assert len(features.index) == 48
    assert features.index.equals(target.index)
    for col in ("month_cos", "month_sin", "hour_cos", "hour_sin"):
        assert col in features.columns
    # Cyclic encodings are always defined (no NaN).
    assert not features[["month_cos", "hour_sin"]].isna().any().any()
