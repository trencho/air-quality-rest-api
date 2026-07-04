"""Hermetic unit tests for the AQI index math (``src/processing/calculate_index``).

Pure functions, no I/O — a good first foothold in the otherwise untested processing
layer. Expected values are computed from the module's own breakpoint table.
"""

import pytest

# Import the config package first so the api/preparation/processing chain initialises
# in order — importing a ``processing`` submodule first hits a circular import.
import api.config  # noqa: F401
from processing.calculate_index import calculate_aqi, calculate_index, to_aqi


def test_to_aqi_linear_interpolation():
    # At the top of a band the value maps to the band's high AQI.
    assert to_aqi(50, 0, 4.4, 0, 4.4) == 50
    # Midway through the pm2_5 51–100 band (c_low=0, c_high=20): 49*15/20 + 51 = 87.75.
    assert to_aqi(100, 51, 20, 0, 15) == 87


@pytest.mark.parametrize(
    "pollutant, value, expected",
    [
        ("co", 0.0, 0),  # zero concentration → 0
        ("co", 2.2, 25),  # half of the first band's ceiling
        ("co", 4.4, 50),  # first band ceiling → 50
        ("pm2_5", 10.0, 50),
        ("pm2_5", 15.0, 87),  # interpolated within the second band
        ("pm2_5", 20.0, 100),  # second band ceiling
        ("pm10", 20.0, 50),
        ("no2", 40.0, 50),
        ("so2", 100.0, 50),
        ("o3", 50.0, 50),
    ],
)
def test_calculate_index(pollutant, value, expected):
    assert calculate_index(pollutant, value) == expected


def test_calculate_index_above_all_breakpoints_returns_zero():
    # Known quirk: a concentration beyond the last breakpoint falls through to 0
    # rather than clamping to 500. Pinned here as current behaviour, not endorsed.
    assert calculate_index("co", 1000.0) == 0


def test_calculate_index_unknown_pollutant_raises():
    with pytest.raises(KeyError):
        calculate_index("unknown", 1.0)


def test_calculate_aqi_returns_max():
    assert calculate_aqi(10, 55, 30) == 55
    assert calculate_aqi(7) == 7
