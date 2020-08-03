from warnings import catch_warnings, simplefilter

from numpy import int64
from pandas import cut as pandas_cut, to_datetime
from tsfresh import extract_features, select_features
from tsfresh.utilities.dataframe_functions import impute

from definitions import dummy_leap_year, seasons


def get_season(time):
    dt = time.date()
    dt = dt.replace(year=dummy_leap_year)

    return next(season for season, (start, end) in seasons if start <= dt <= end)


def encode_categorical_data(dataframe):
    obj_columns = dataframe.select_dtypes(['object']).columns
    dataframe[obj_columns] = dataframe.select_dtypes(['object']).apply(lambda x: x.astype('category'))
    cat_columns = dataframe.select_dtypes(['category']).columns
    dataframe[cat_columns] = dataframe[cat_columns].apply(lambda x: x.cat.codes)


def generate_calendar_features(dataframe):
    dataframe['time'] = to_datetime(dataframe['time'], unit='s')

    dataframe['month'] = dataframe['time'].dt.month
    dataframe['day'] = dataframe['time'].dt.day
    dataframe['hour'] = dataframe['time'].dt.hour
    dataframe['weekOfYear'] = dataframe['time'].dt.weekofyear
    dataframe['dayOfWeek'] = dataframe['time'].dt.dayofweek
    dataframe['dayOfYear'] = dataframe['time'].dt.dayofyear
    dataframe['weekdayName'] = dataframe['time'].dt.day_name()
    dataframe['quarter'] = dataframe['time'].dt.quarter
    dataframe['daysInMonth'] = dataframe['time'].dt.days_in_month
    dataframe['isMonthStart'] = dataframe['time'].dt.is_month_start
    dataframe['isMonthEnd'] = dataframe['time'].dt.is_month_end
    dataframe['isQuarterStart'] = dataframe['time'].dt.is_quarter_start
    dataframe['isQuarterEnd'] = dataframe['time'].dt.is_quarter_end
    dataframe['isYearStart'] = dataframe['time'].dt.is_year_start
    dataframe['isYearEnd'] = dataframe['time'].dt.is_year_end
    dataframe['isLeapYear'] = dataframe['time'].dt.is_leap_year
    dataframe['isWeekend'] = dataframe['time'].apply(lambda x: 0 if to_datetime(x).weekday() in (5, 6) else 1)
    dataframe['season'] = dataframe['time'].apply(get_season)

    bins = [0, 4, 8, 12, 16, 20, 24]
    labels = ['Late Night', 'Early Morning', 'Morning', 'Noon', 'Eve', 'Night']
    dataframe['session'] = pandas_cut(dataframe['hour'], bins=bins, labels=labels)

    dataframe['time'] = dataframe['time'].values.astype(int64) // 10 ** 9

    encode_categorical_data(dataframe)


def select_tsfresh_features(dataframe, target):
    validation_split = len(dataframe) * 3 // 4

    train_x = dataframe.iloc[:validation_split].drop(columns=target)
    train_y = dataframe.iloc[:validation_split][target]

    train_features_selected = select_features(train_x, train_y)
    return dataframe[train_features_selected]


def generate_tsfresh_features(dataframe, target):
    y = dataframe[target]
    dataframe.drop(columns=target, inplace=True)

    dataframe = dataframe.stack()
    dataframe.index.rename(['id', 'time'], inplace=True)
    dataframe = dataframe.reset_index()

    with catch_warnings():
        simplefilter('ignore')
        dataframe = extract_features(dataframe, column_id='id', column_sort='time')

    dataframe = impute(dataframe)
    dataframe[target] = y

    dataframe = select_tsfresh_features(dataframe, target)
    encode_categorical_data(dataframe)

    return dataframe


def generate_features(dataframe):
    generate_calendar_features(dataframe)
    # dataframe = generate_tsfresh_features(dataframe, pollutant)

    dataframe.drop(columns=['precipAccumulation', 'time'], inplace=True, errors='ignore')
