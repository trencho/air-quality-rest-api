"""Hermetic unit tests for the pure helpers in ``modeling/train_model``.

The training orchestration itself (hyper-parameter search, model persistence, plots)
is not exercised here — only the small, I/O-free frame transform it relies on.
"""

from pandas import DataFrame

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a package submodule first can hit a circular import.
import api.config  # noqa: F401
from modeling.train_model import previous_value_overwrite


def test_previous_value_overwrite_shifts_up_and_drops_last_row():
    # Each row takes the next row's values (shift up by one); the trailing NaN row
    # that leaves is dropped, so an n-row frame becomes n-1 rows.
    dataframe = DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    result = previous_value_overwrite(dataframe)
    assert result.to_dict("list") == {"a": [2.0, 3.0], "b": [5.0, 6.0]}
    assert len(result.index) == 2
