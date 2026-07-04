"""Hermetic unit tests for the pure helpers in ``src/processing/normalize_data``.

``flatten_json`` and the hour-rounding helpers are deterministic and I/O-free (the
heavy ``process_data`` pipeline around them is not covered here). ``next_hour`` /
``closest_hour`` take an explicit datetime so they're pinned exactly; ``current_hour``
reads the clock, so only its truncation invariant is asserted.
"""

from datetime import datetime

import pytest

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a ``processing`` submodule first hits a circular import.
import api.config  # noqa: F401
from processing.normalize_data import (
    closest_hour,
    current_hour,
    flatten_json,
    next_hour,
)


@pytest.mark.parametrize(
    "nested, expected",
    [
        ({"a": 1, "b": {"c": 2}}, {"a": 1, "b_c": 2}),  # nested dict → underscore path
        ({"a": [{"x": 1}]}, {"a_x": 1}),  # single-element list collapses (no index)
        ({"a": [1, 2]}, {"a_0": 1, "a_1": 2}),  # multi-element list → indexed keys
    ],
)
def test_flatten_json(nested, expected):
    assert flatten_json(nested) == expected


def test_flatten_json_excludes_keys():
    assert flatten_json({"a": 1, "secret": 2}, exclude=["secret"]) == {"a": 1}


def test_next_hour_truncates_and_adds_one_hour():
    assert next_hour(datetime(2024, 1, 1, 10, 30)) == datetime(2024, 1, 1, 11, 0)


@pytest.mark.parametrize(
    "minute, expected_hour",
    [
        (20, 10),  # < 30 minutes rounds down
        (29, 10),
        (30, 11),  # >= 30 minutes rounds up
        (45, 11),
    ],
)
def test_closest_hour_rounds_to_nearest(minute, expected_hour):
    result = closest_hour(datetime(2024, 1, 1, 10, minute))
    assert result == datetime(2024, 1, 1, expected_hour, 0)


def test_current_hour_is_truncated_to_the_hour():
    now_hour = current_hour()
    assert now_hour.minute == 0
    assert now_hour.second == 0
    assert now_hour.microsecond == 0
