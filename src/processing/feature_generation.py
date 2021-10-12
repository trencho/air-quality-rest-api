from datetime import date, datetime
from warnings import catch_warnings, simplefilter

from numpy import abs
from pandas import cut, DataFrame, Int64Index, Series
from statsmodels.tsa.stattools import pacf
from tsfresh import extract_features, select_features
from tsfresh.utilities.dataframe_functions import impute


def get_season(time: datetime) -> str:
    dummy_leap_year = 2000

    dt = time.date()
    dt = dt.replace(year=dummy_leap_year)

    seasons = [
        ('winter', (date(dummy_leap_year, 1, 1), date(dummy_leap_year, 3, 20))),
        ('spring', (date(dummy_leap_year, 3, 21), date(dummy_leap_year, 6, 20))),
        ('summer', (date(dummy_leap_year, 6, 21), date(dummy_leap_year, 9, 22))),
        ('autumn', (date(dummy_leap_year, 9, 23), date(dummy_leap_year, 12, 20))),
        ('winter', (date(dummy_leap_year, 12, 21), date(dummy_leap_year, 12, 31)))
    ]
    return next(season for season, (start, end) in seasons if start <= dt <= end)


def encode_categorical_data(dataframe: DataFrame) -> None:
    obj_columns = dataframe.select_dtypes('object').columns
    dataframe[obj_columns] = dataframe[obj_columns].astype('category')
    cat_columns = dataframe.select_dtypes('category').columns
    dataframe[cat_columns] = dataframe[cat_columns].apply(lambda x: x.cat.codes)


def generate_lag_features(target: Series, lags: int) -> DataFrame:
    partial = Series(data=pacf(target, nlags=lags if lags < target.size // 2 else target.size // 2 - 1))
    lags = [*partial[abs(partial) >= 0.2].index]

    if 0 in lags:
        lags.remove(0)

    features = DataFrame()
    for lag in lags:
        features[f'lag_{lag}'] = target.shift(lag)

    return features


def generate_time_features(target) -> DataFrame:
    features = DataFrame()
    features['month'] = target.index.month
    features['day'] = target.index.day
    features['hour'] = target.index.hour
    features['weekOfYear'] = Int64Index(target.index.isocalendar().week)
    features['dayOfWeek'] = target.index.dayofweek
    features['dayOfYear'] = target.index.dayofyear
    features['weekdayName'] = target.index.day_name()
    features['quarter'] = target.index.quarter
    features['daysInMonth'] = target.index.days_in_month
    features['isMonthStart'] = target.index.is_month_start
    features['isMonthEnd'] = target.index.is_month_end
    features['isQuarterStart'] = target.index.is_quarter_start
    features['isQuarterEnd'] = target.index.is_quarter_end
    features['isYearStart'] = target.index.is_year_start
    features['isYearEnd'] = target.index.is_year_end
    features['isLeapYear'] = target.index.is_leap_year
    features['isWeekend'] = target.index.to_series().apply(lambda x: 0 if x.dayofweek in (5, 6) else 1).values
    features['season'] = target.index.to_series().apply(get_season).values

    bins = [0, 4, 8, 12, 16, 20, 24]
    labels = ['Late Night', 'Early Morning', 'Morning', 'Noon', 'Eve', 'Night']
    features['session'] = cut(features['hour'], bins=bins, labels=labels)

    features.set_index(target.index, inplace=True)

    return features


def select_time_series_features(dataframe: DataFrame, target: str) -> DataFrame:
    validation_split = len(dataframe) * 3 // 4

    train_x = dataframe.iloc[:validation_split].drop(columns=target)
    train_y = dataframe.iloc[:validation_split][target]

    return select_features(train_x, train_y)


def generate_time_series_features(dataframe: DataFrame, target: str) -> DataFrame:
    y = dataframe[target]
    features = dataframe.drop(columns=target)

    features = features.stack()
    features.index.rename(['id', 'time'], inplace=True)
    features.reset_index(inplace=True)

    with catch_warnings():
        simplefilter('ignore')
        features = extract_features(features, column_id='id', column_sort='time')

    features = impute(features)
    features[target] = y

    return select_time_series_features(features, target)


def generate_features(target: Series, lags: int = 24) -> DataFrame:
    lag_features = generate_lag_features(target, lags)
    time_features = generate_time_features(target)
    features = lag_features.join(time_features, how='inner')

    return features.dropna(axis='columns', how='all').dropna(axis='index', how='any')
