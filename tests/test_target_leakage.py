"""Guard against the target reaching the feature matrix.

`split_dataframe` once shifted X forward a row and left y in place, which paired features at t+1
with a target at t. `lag_1` at t+1 IS the value at t, so the target became a column of X and every
recorded error was near-zero by construction.

The assertion is on CORRELATION, not equality. `split_dataframe` scales X through a RobustScaler,
so a leaked column is no longer numerically equal to y while carrying exactly the same information;
an `allclose` check passes on the broken code. The honest-lag control is part of the test rather
than a comment: a pollutant series is close to a random walk, so an ordinary lag already correlates
at ~0.997, and only the shift turns that into identity.
"""

from numpy import corrcoef, cumsum
from numpy.random import default_rng
from pandas import DataFrame, date_range

from modeling.train_model import split_dataframe
from processing.feature_generation import generate_features

LEAK_THRESHOLD = 0.9999


def _random_walk_frame(rows: int = 400, pollutant: str = "pm10") -> DataFrame:
    rng = default_rng(7)
    series = cumsum(rng.normal(0, 1, rows)) + 50.0
    frame = DataFrame(
        {pollutant: series}, index=date_range("2026-01-01", periods=rows, freq="h")
    )
    frame = frame.join(generate_features(frame[pollutant]), how="inner")
    return frame.dropna(axis="columns", how="all").dropna(axis="index", how="any")


def test_no_feature_carries_the_target():
    frame = _random_walk_frame()
    x, y, _ = split_dataframe(frame, "pm10")

    worst_column, worst_r = None, -1.0
    for column in x.columns:
        r = abs(corrcoef(x[column].to_numpy(float), y.to_numpy(float))[0, 1])
        if r > worst_r:
            worst_column, worst_r = column, r

    assert worst_r < LEAK_THRESHOLD, (
        f"{worst_column} correlates with the target at r={worst_r:.6f}; "
        "the target has reached the feature matrix"
    )


def test_the_control_is_high_so_the_threshold_discriminates():
    """An honest lag_1 correlates at ~0.997, well under the threshold.

    Without this, a threshold of 0.9999 could be passing because the features are uninformative
    rather than because the leak is gone.
    """
    frame = _random_walk_frame()
    r = abs(
        corrcoef(frame["lag_1"].to_numpy(float), frame["pm10"].to_numpy(float))[0, 1]
    )
    assert 0.9 < r < LEAK_THRESHOLD, f"control lag_1 correlation was {r:.6f}"
