import warnings
from datetime import datetime

import pandas as pd
from tsfresh import extract_features, select_features
from tsfresh.utilities.dataframe_functions import impute

from definitions import dummy_leap_year, seasons


def get_season(time):
    dt = datetime.fromtimestamp(time)
    dt = dt.date()
    dt = dt.replace(year=dummy_leap_year)

    return next(season for season, (start, end) in seasons if start <= dt <= end)


def generate_calendar_features(dataframe):
    dataframe = dataframe.copy()
    dataframe['hour'] = dataframe['time'].dt.hour
    dataframe['month'] = dataframe['time'].dt.month
    dataframe['dayOfWeek'] = dataframe['time'].dt.dayofweek
    dataframe['dayOfYear'] = dataframe['time'].dt.dayofyear
    dataframe['weekOfYear'] = dataframe['time'].dt.weekofyear
    dataframe['isWeekend'] = dataframe['time'].apply(lambda x: 1 if pd.to_datetime(x).weekday() in (5, 6) else 0)
    dataframe['season'] = dataframe['time'].apply(get_season)

    bins = [0, 4, 8, 12, 16, 20, 24]
    labels = ['Late Night', 'Early Morning', 'Morning', 'Noon', 'Eve', 'Night']
    dataframe['session'] = pd.cut(dataframe['hour'], bins=bins, labels=labels)
    dataframe['session'] = dataframe['session'].astype('category')

    return dataframe


def select_tsfresh_features(dataframe, target):
    validation_split_i = len(dataframe) * 3 / 4

    train_x = dataframe.iloc[:validation_split_i].drop(target, axis=1)
    train_y = dataframe.iloc[:validation_split_i][target]

    train_features_selected = select_features(train_x, train_y)
    dataframe = dataframe[train_features_selected]

    return dataframe


def generate_tsfresh_features(dataframe, target):
    y = dataframe[target]
    dataframe.drop(target, axis=1, inplace=True)

    dataframe = dataframe.stack()
    dataframe.index.rename(['id', 'time'], inplace=True)
    dataframe = dataframe.reset_index()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dataframe = extract_features(dataframe, column_id="id", column_sort="time")

    dataframe = impute(dataframe)
    dataframe[target] = y

    dataframe = select_tsfresh_features(dataframe, target)

    return dataframe


def generate_features(dataframe, pollutant):
    dataframe = dataframe.copy()

    dataframe['prevValue'] = dataframe[pollutant].shift(1)
    dataframe['prevValue'].interpolate(method='nearest', fill_value='extrapolate', inplace=True)

    dataframe = generate_calendar_features(dataframe)
    dataframe = generate_tsfresh_features(dataframe, pollutant)

    dataframe['icon'] = dataframe['icon'].astype('category')
    dataframe['precipType'] = dataframe['precipType'].astype('category')
    dataframe['summary'] = dataframe['summary'].astype('category')

    cat_columns = dataframe.select_dtypes(['category']).columns
    dataframe[cat_columns] = dataframe[cat_columns].apply(lambda x: x.cat.codes)

    return dataframe
