from datetime import date
from warnings import catch_warnings, simplefilter

from pandas import cut as pandas_cut, to_datetime
from tsfresh import extract_features, select_features
from tsfresh.utilities.dataframe_functions import impute


def get_season(time):
    dummy_leap_year = 2000  # dummy leap year to allow input X-02-29 (leap day)

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
    obj_columns = dataframe.select_dtypes(['object']).columns
    dataframe[obj_columns] = dataframe.select_dtypes(['object']).apply(lambda x: x.astype('category'))
    cat_columns = dataframe.select_dtypes(['category']).columns
    dataframe[cat_columns] = dataframe[cat_columns].apply(lambda x: x.cat.codes)


def generate_time_features(dataframe):
    dataframe['time'] = to_datetime(dataframe['time'], unit='s')

    dataframe['month'] = dataframe['time'].dt.month
    dataframe['day'] = dataframe['time'].dt.day
    dataframe['hour'] = dataframe['time'].dt.hour
    dataframe['weekOfYear'] = dataframe['time'].dt.isocalendar().week
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

    dataframe.drop(columns=['time'], inplace=True, errors='ignore')

    encode_categorical_data(dataframe)


def select_time_series_features(dataframe, target):
    validation_split = len(dataframe) * 3 // 4

    train_x = dataframe.iloc[:validation_split].drop(columns=target)
    train_y = dataframe.iloc[:validation_split][target]

    return select_features(train_x, train_y)


def generate_time_series_features(dataframe, target):
    y = dataframe[target]
    dataframe.drop(columns=target, inplace=True)

    dataframe = dataframe.stack()
    dataframe.index.rename(['id', 'time'], inplace=True)
    dataframe.reset_index(inplace=True)

    with catch_warnings():
        simplefilter('ignore')
        dataframe = extract_features(dataframe, column_id='id', column_sort='time')

    dataframe = impute(dataframe)
    dataframe[target] = y

    dataframe = select_time_series_features(dataframe, target)
    encode_categorical_data(dataframe)

    return dataframe


def generate_features(dataframe):
    generate_time_features(dataframe)
    # dataframe = generate_time_series_features(dataframe, pollutant)
