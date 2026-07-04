"""Hermetic unit tests for the pure metric helpers in ``modeling/process_results``.

Covers the invalid-value filtering and MAPE computation; the CSV-writing
``save_errors``/``save_results`` are not exercised here.
"""

import numpy as np
import pytest

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a package submodule first can hit a circular import.
import api.config  # noqa: F401
from modeling.process_results import (
    filter_invalid_values,
    mean_absolute_percentage_error,
)


def test_filter_invalid_values_drops_inf_and_nan_rows():
    y_true = np.array([1.0, 2.0, np.inf, 4.0])
    y_predicted = np.array([1.0, 2.0, 3.0, np.nan])
    filtered_true, filtered_predicted = filter_invalid_values(y_true, y_predicted)
    # The inf (row 2) and nan (row 3) rows are removed on either side.
    assert filtered_true.tolist() == [1.0, 2.0]
    assert filtered_predicted.tolist() == [1.0, 2.0]


def test_mean_absolute_percentage_error():
    result = mean_absolute_percentage_error(
        np.array([100.0, 200.0]), np.array([110.0, 180.0])
    )
    assert result == pytest.approx(10.0)


def test_mean_absolute_percentage_error_div_by_zero_returns_none():
    with np.errstate(divide="ignore", invalid="ignore"):
        result = mean_absolute_percentage_error(np.array([0.0]), np.array([5.0]))
    assert result is None
