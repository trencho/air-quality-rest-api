"""Characterization tests for ``src/processing/feature_imputation``.

This module was the least-covered file in the project (11%) and had no test file at
all, while carrying the numeric core of the imputation step: a Gower-style distance
matrix and a k-nearest-neighbour fill.

They are characterization tests on purpose. They pin what the code does TODAY rather
than assert what it ought to do, because the point is to make a later change visible:
every validation path here returns ``None`` after logging, which is indistinguishable
from "worked and produced nothing" to a caller that does not check. Narrowing the broad
``except`` blocks in this package, or touching the distance maths, should either keep
these green or fail loudly and deliberately.

The distance values themselves are asserted structurally (symmetry, NaN diagonal,
shape) rather than by copying floats out of a run: pinning a matrix of magic numbers
would fail on any harmless refactor and teach nothing about what broke.
"""

import numpy as np
import pytest
from pandas import DataFrame, Series

# Import the config package first so the api/preparation/processing chain initialises in
# order -- importing a processing submodule first hits a circular import.
import api.config  # noqa: F401
from processing.feature_imputation import distance_matrix, knn_impute, weighted_hamming


@pytest.fixture
def numeric_frame():
    """Six rows of two well-separated numeric attributes."""
    return DataFrame(
        {
            "a": [1.0, 1.1, 1.2, 9.0, 9.1, 9.2],
            "b": [2.0, 2.1, 2.2, 8.0, 8.1, 8.2],
        }
    )


# --- distance_matrix ---------------------------------------------------------------


def test_distance_matrix_is_square_symmetric_and_nan_on_the_diagonal(numeric_frame):
    result = distance_matrix(numeric_frame)

    assert result is not None
    assert result.shape == (6, 6)
    values = result.to_numpy()
    # The diagonal is NaN, not 0, and that is deliberate (`fill_diagonal(result, nan)`):
    # knn_impute takes the k smallest distances, and numpy's argsort sorts NaN last, so
    # a NaN self-distance is what stops a row being its own nearest neighbour. A
    # "tidier" zero diagonal would make every point its own closest match and impute
    # each gap from itself.
    assert np.isnan(np.diag(values)).all()
    # Symmetry ignoring the NaN diagonal: distance is a property of the pair.
    off_diagonal = ~np.eye(6, dtype=bool)
    assert np.allclose(values[off_diagonal], values.T[off_diagonal])


def test_distance_matrix_separates_two_clusters(numeric_frame):
    values = distance_matrix(numeric_frame).to_numpy()

    # Rows 0-2 and rows 3-5 are far apart in both attributes; within-cluster distance
    # must be smaller than across-cluster distance, whatever the metric's scale.
    assert values[0, 1] < values[0, 4]
    assert values[5, 4] < values[5, 1]


def test_distance_matrix_rejects_an_unsupported_numeric_metric(numeric_frame):
    # Returns None rather than raising, so a caller that does not check gets a silent
    # nothing. Pinned deliberately: this is the behaviour a broad `except` upstream
    # would otherwise hide.
    assert distance_matrix(numeric_frame, numeric_distance="mahalanobis") is None


def test_distance_matrix_rejects_an_unsupported_categorical_metric(numeric_frame):
    assert distance_matrix(numeric_frame, categorical_distance="levenshtein") is None


def test_weighted_hamming_returns_one_row_and_column_per_observation():
    frame = DataFrame({"city": ["skopje", "bitola", "skopje", "ohrid"]})

    result = weighted_hamming(frame)

    assert result.shape == (4, 4)
    # Identical categories are closer to each other than to a different one: rows 0 and
    # 2 are both "skopje".
    assert result[0][2] < result[0][1]


# --- knn_impute: the parameter guards, all of which return None ---------------------


def test_knn_impute_refuses_fewer_than_three_observations():
    target = Series([1.0, None])
    attributes = DataFrame({"a": [1.0, 2.0]})

    assert knn_impute(target, attributes, k_neighbors=1) is None


def test_knn_impute_refuses_attributes_of_a_different_length(numeric_frame):
    target = Series([1.0, None, 3.0])  # three rows against the fixture's six

    assert knn_impute(target, numeric_frame, k_neighbors=2) is None


@pytest.mark.parametrize("k_neighbors", [0, -1, 7])
def test_knn_impute_refuses_a_neighbour_count_outside_the_data(
    numeric_frame, k_neighbors
):
    target = Series([1.0, None, 3.0, 4.0, 5.0, 6.0])

    assert knn_impute(target, numeric_frame, k_neighbors=k_neighbors) is None


def test_knn_impute_refuses_an_unknown_aggregation_method(numeric_frame):
    target = Series([1.0, None, 3.0, 4.0, 5.0, 6.0])

    assert knn_impute(target, numeric_frame, 2, aggregation_method="geometric") is None


def test_knn_impute_refuses_a_categorical_target_unless_aggregating_by_mode(
    numeric_frame,
):
    target = Series(["low", None, "high", "low", "high", "low"])

    assert knn_impute(target, numeric_frame, 2, aggregation_method="mean") is None


def test_knn_impute_propagates_a_none_distance_matrix(numeric_frame):
    # An invalid metric makes distance_matrix return None; knn_impute must pass that
    # through rather than continue with nothing.
    target = Series([1.0, None, 3.0, 4.0, 5.0, 6.0])

    assert knn_impute(target, numeric_frame, 2, numeric_distance="mahalanobis") is None


# --- knn_impute: the imputation itself ----------------------------------------------


def test_knn_impute_fills_a_gap_from_its_nearest_neighbours(numeric_frame):
    # Row 1 sits in the first cluster, so its two nearest rows are 0 and 2 (values 10
    # and 12), and the mean of those is 11. k=2 on purpose: with k=3 the third-nearest
    # row is already in the FAR cluster (a distance of ~9.9 against ~0.14), which drags
    # the fill to ~37 -- worth knowing, because it is the k, not the metric, that
    # decides whether a gap is filled from its own cluster.
    target = Series([10.0, None, 12.0, 90.0, 91.0, 92.0])

    result = knn_impute(target, numeric_frame, k_neighbors=2)

    assert result is not None
    assert result.iloc[1, 0] == pytest.approx(11.0)


def test_knn_impute_leaves_the_value_missing_when_too_many_neighbours_are_missing(
    numeric_frame,
):
    # Every value in the first cluster is missing, so for row 1 at least half of the
    # three nearest neighbours are also missing and the threshold branch declines to
    # invent a number. Guessing here would be worse than a gap.
    target = Series([None, None, None, 90.0, 91.0, 92.0])

    result = knn_impute(target, numeric_frame, k_neighbors=3)

    assert result is not None
    assert bool(result.iloc[:3, 0].isnull().all())


def test_knn_impute_leaves_present_values_untouched(numeric_frame):
    target = Series([10.0, 11.0, 12.0, 90.0, 91.0, 92.0])

    result = knn_impute(target, numeric_frame, k_neighbors=3)

    assert result is not None
    assert list(result.iloc[:, 0]) == [10.0, 11.0, 12.0, 90.0, 91.0, 92.0]
