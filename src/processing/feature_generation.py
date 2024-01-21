from datetime import date, datetime

from numpy import abs, cos, pi, sin
from pandas import cut, DataFrame, Index, Series
from statsmodels.tsa.stattools import pacf


def get_season(time: datetime) -> str:
    # Dummy leap year to allow input 29-02-X (leap day)
    dummy_leap_year = 2000

    dt = time.date()
    dt = dt.replace(year=dummy_leap_year)

    seasons = [
        ("winter", (date(dummy_leap_year, 1, 1), date(dummy_leap_year, 3, 20))),
        ("spring", (date(dummy_leap_year, 3, 21), date(dummy_leap_year, 6, 20))),
        ("summer", (date(dummy_leap_year, 6, 21), date(dummy_leap_year, 9, 22))),
        ("autumn", (date(dummy_leap_year, 9, 23), date(dummy_leap_year, 12, 20))),
        ("winter", (date(dummy_leap_year, 12, 21), date(dummy_leap_year, 12, 31)))
    ]
    return next(season for season, (start, end) in seasons if start <= dt <= end)


def encode_categorical_data(dataframe: DataFrame) -> None:
    obj_columns = dataframe.select_dtypes("object").columns
    dataframe[obj_columns] = dataframe[obj_columns].astype("category")
    cat_columns = dataframe.select_dtypes("category").columns
    dataframe[cat_columns] = dataframe[cat_columns].apply(lambda x: x.cat.codes, engine="numba",
                                                          engine_kwargs={"parallel": True})


def encode_cyclic_data(features: DataFrame, col: str, data: [DataFrame, Series], max_value: int) -> None:
    features[f"{col}_cos"] = cos(2 * pi * data / max_value)
    features[f"{col}_sin"] = sin(2 * pi * data / max_value)


def generate_lag_features(target: Series, lags: int) -> DataFrame:
    partial = Series(data=pacf(target, nlags=lags if lags < target.size // 2 else target.size // 2 - 1))
    lags = list(partial[abs(partial) >= 0.2].index)

    if 0 in lags:
        # Do not consider itself as lag feature
        lags.remove(0)

    features = DataFrame()
    for lag in lags:
        features[f"lag_{lag}"] = target.shift(lag)

    return features


def generate_time_features(target) -> DataFrame:
    features = DataFrame()
    encode_cyclic_data(features, "month", target.index.month, 12)
    encode_cyclic_data(features, "day", target.index.day, 30)
    encode_cyclic_data(features, "hour", target.index.hour, 24)
    encode_cyclic_data(features, "week_of_year", Index(target.index.isocalendar().week, dtype="int64"), 52)
    encode_cyclic_data(features, "day_of_week", target.index.dayofweek, 7)
    encode_cyclic_data(features, "day_of_year", target.index.dayofyear, 365)
    encode_cyclic_data(features, "quarter", target.index.quarter, 4)
    encode_cyclic_data(features, "days_in_month", target.index.days_in_month, 30)
    features["isMonthStart"] = target.index.is_month_start
    features["isMonthEnd"] = target.index.is_month_end
    features["isQuarterStart"] = target.index.is_quarter_start
    features["isQuarterEnd"] = target.index.is_quarter_end
    features["isYearStart"] = target.index.is_year_start
    features["isYearEnd"] = target.index.is_year_end
    features["isLeapYear"] = target.index.is_leap_year
    features["isWeekend"] = target.index.to_series().apply(lambda x: 0 if x.dayofweek in (5, 6) else 1).values

    season = DataFrame(target.index.to_series().apply(get_season).values)
    encode_categorical_data(season)
    encode_cyclic_data(features, "season", season, 4)

    bins = [0, 4, 8, 12, 16, 20, 24]
    labels = ["Late Night", "Early Morning", "Morning", "Noon", "Eve", "Night"]
    session = DataFrame(cut(target.index.hour, bins=bins, labels=labels, include_lowest=True))
    encode_categorical_data(session)
    encode_cyclic_data(features, "session", session, len(labels))

    features.set_index(target.index, inplace=True)

    return features


def generate_features(target: Series, lags: int = 24) -> DataFrame:
    lag_features = generate_lag_features(target, lags)
    time_features = generate_time_features(target)
    features = time_features if len(lag_features.index) == 0 else lag_features.join(time_features, how="inner")

    return features
