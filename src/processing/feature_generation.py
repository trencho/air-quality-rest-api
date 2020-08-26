from datetime import date
from warnings import catch_warnings, simplefilter

from numpy import abs
from pandas import cut as pandas_cut, DataFrame, Series
from statsmodels.tsa.stattools import pacf
from tsfresh import extract_features, select_features
from tsfresh.utilities.dataframe_functions import impute


def get_season(time):
    dummy_leap_year = 2000  # Dummy leap year to allow input 29-02-X (leap day)

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


def encode_categorical_data(dataframe):
    obj_columns = dataframe.select_dtypes('object').columns
    dataframe[obj_columns] = dataframe.select_dtypes('object').apply(lambda x: x.astype('category'))
    cat_columns = dataframe.select_dtypes('category').columns
    dataframe[cat_columns] = dataframe[cat_columns].apply(lambda x: x.cat.codes)


def generate_lag_features(target, lags=48):
    partial = Series(data=pacf(target, nlags=lags))
    lags = list(partial[abs(partial) >= 0.2].index)

    if 0 in lags:
        lags.remove(0)  # Do not consider itself as lag feature

    features = DataFrame()
    for lag in lags:
        features[f'lag_{lag}'] = target.shift(lag)

    return features


def generate_time_features(target):
    features = DataFrame()
    features['month'] = target.index.month
    features['day'] = target.index.day
    features['hour'] = target.index.hour
    # features['weekOfYear'] = Int64Index(target.index.isocalendar().week)
    features['weekOfYear'] = target.index.weekofyear
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
    features['session'] = pandas_cut(features['hour'], bins=bins, labels=labels)

    features.set_index(target.index, inplace=True)

    return features


def select_time_series_features(dataframe, target):
    validation_split = len(dataframe) * 3 // 4

    train_x = dataframe.iloc[:validation_split].drop(columns=target)
    train_y = dataframe.iloc[:validation_split][target]

    return select_features(train_x, train_y)


def generate_time_series_features(dataframe, target):
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

    features = select_time_series_features(features, target)

    return features


def generate_features(target):
    lag_features = generate_lag_features(target)
    time_features = generate_time_features(target)

    dataframe = lag_features.join(time_features, how='outer').dropna()
    encode_categorical_data(dataframe)

    return dataframe
