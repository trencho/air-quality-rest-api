import warnings

import numpy as np
import pandas as pd
from tsfresh import extract_features, select_features
from tsfresh.utilities.dataframe_functions import impute

from definitions import dummy_leap_year, seasons


def encode_categorical_data(dataframe):
    obj_columns = dataframe.select_dtypes(['object']).columns
    dataframe[obj_columns] = dataframe.select_dtypes(['object']).apply(lambda x: x.astype('category'))
    cat_columns = dataframe.select_dtypes(['category']).columns
    dataframe[cat_columns] = dataframe[cat_columns].apply(lambda x: x.cat.codes)

    return dataframe


def get_season(time):
    dt = time.date()
    dt = dt.replace(year=dummy_leap_year)

    return next(season for season, (start, end) in seasons if start <= dt <= end)


def generate_calendar_features(dataframe):
    dataframe = dataframe.copy()
    dataframe['time'] = pd.to_datetime(dataframe['time'], unit='s')

    dataframe['hour'] = dataframe['time'].dt.hour
    dataframe['month'] = dataframe['time'].dt.month
    dataframe['dayOfWeek'] = dataframe['time'].dt.dayofweek
    dataframe['dayOfYear'] = dataframe['time'].dt.dayofyear
    dataframe['weekOfYear'] = dataframe['time'].dt.weekofyear
    dataframe['isWeekend'] = dataframe['time'].apply(lambda x: 0 if pd.to_datetime(x).weekday() in (5, 6) else 1)
    dataframe['season'] = dataframe['time'].apply(get_season)
    dataframe['season'] = dataframe['season'].astype('category')

    dataframe['time'] = dataframe['time'].values.astype(np.int64) // 10 ** 9

    bins = [0, 4, 8, 12, 16, 20, 24]
    labels = ['Late Night', 'Early Morning', 'Morning', 'Noon', 'Eve', 'Night']
    dataframe['session'] = pd.cut(dataframe['hour'], bins=bins, labels=labels)
    dataframe['session'] = dataframe['session'].astype('category')

    dataframe = encode_categorical_data(dataframe)

    return dataframe


def select_tsfresh_features(dataframe, target):
    validation_split = len(dataframe) * 3 // 4

    train_x = dataframe.iloc[:validation_split].drop(target, axis=1)
    train_y = dataframe.iloc[:validation_split][target]

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

    dataframe = encode_categorical_data(dataframe)

    return dataframe


def generate_features(dataframe):
    dataframe = dataframe.copy()

    dataframe = generate_calendar_features(dataframe)
    # dataframe = generate_tsfresh_features(dataframe, pollutant)

    dataframe = dataframe.drop(columns='precipAccumulation', errors='ignore')
    dataframe = dataframe.drop(columns='time', errors='ignore')

    return dataframe
