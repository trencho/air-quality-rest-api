from datetime import datetime
from os import path

from numpy import abs, nan, number
from pandas import read_csv, to_numeric
from scipy.stats import zscore
from sklearn.impute import KNNImputer

from definitions import DATA_PROCESSED_PATH, DATA_RAW_PATH, pollutants
from preparation import trim_dataframe
from .calculate_index import calculate_aqi, calculate_co_index, calculate_no2_index, calculate_o3_index, \
    calculate_pm2_5_index, calculate_pm10_index, calculate_so2_index


def closest_hour(t: datetime) -> datetime:
    return t.replace(hour=t.hour if t.minute <= 30 else 0 if t.hour == 23 else t.hour + 1, minute=0, second=0,
                     microsecond=0)


def current_hour() -> datetime:
    t = datetime.now()
    return t.replace(hour=t.hour, minute=0, second=0, microsecond=0)


def drop_numerical_outliers(dataframe, z_thresh=3):
    constrains = dataframe.select_dtypes(include=[number]).apply(lambda x: abs(zscore(x)) < z_thresh,
                                                                 result_type='reduce').all(axis=1)
    dataframe.drop(index=dataframe.index[~constrains], inplace=True)


def flatten_json(nested_json: dict, exclude=None) -> dict:
    """
    Flatten a list of nested dicts.
    """
    if exclude is None:
        exclude = ['']
    out = {}

    def flatten(x: (list, dict, str), name: str = '', exclude=exclude) -> None:
        if type(x) is dict:
            for a in x:
                if a not in exclude:
                    flatten(x[a], f'{name}{a}_')
        elif type(x) is list:
            if len(x) == 1:
                flatten(x[0], f'{name}')
            else:
                i = 0
                for a in x:
                    flatten(a, f'{name}{i}_')
                    i += 1
        else:
            out[name[:-1]] = x

    flatten(nested_json)
    return out


def next_hour(t: datetime) -> datetime:
    return t.replace(day=t.day + 1 if t.hour == 23 else t.day, hour=0 if t.hour == 23 else t.hour + 1, minute=0,
                     second=0, microsecond=0)


def process_data(city_name: str, sensor_id: str, collection: str) -> None:
    try:
        dataframe = read_csv(path.join(DATA_RAW_PATH, city_name, sensor_id, f'{collection}.csv'))
    except FileNotFoundError:
        return

    collection_path = path.join(DATA_PROCESSED_PATH, city_name, sensor_id, f'{collection}.csv')
    if path.exists(collection_path):
        dataframe = dataframe.append(read_csv(collection_path), ignore_index=True, sort=True)

    df_columns = dataframe.columns.copy()
    df_columns = df_columns.drop(['aqi', 'icon', 'precipType', 'summary'], errors='ignore')

    imp = KNNImputer()
    for column in df_columns:
        dataframe[column] = to_numeric(dataframe[column], errors='coerce')
        if not dataframe[column].isna().any():
            continue
        if not dataframe[column].isna().all():
            dataframe[column] = imp.fit_transform(dataframe[column].values.reshape(-1, 1))
            dataframe[column].interpolate(method='nearest', fill_value='extrapolate', inplace=True)
        else:
            dataframe.drop(columns=column, inplace=True, errors='ignore')

    pollutants_wo_aqi = pollutants.copy()
    pollutants_wo_aqi.pop('aqi')
    columns = pollutants_wo_aqi.copy()
    for column in columns:
        if column not in dataframe.columns:
            pollutants_wo_aqi.pop(column)

    drop_columns_std = dataframe[pollutants_wo_aqi].std()[dataframe[pollutants_wo_aqi].std() == 0].index.values

    dataframe[pollutants_wo_aqi].replace(0, nan).bfill(inplace=True)
    dataframe[pollutants_wo_aqi].replace(0, nan).ffill(inplace=True)
    dataframe.drop(columns=drop_columns_std, inplace=True)

    dataframe['aqi'] = dataframe.apply(
        lambda row: calculate_aqi(calculate_co_index(row['co']) if 'co' in dataframe.columns else 0,
                                  calculate_no2_index(row['no2']) if 'no2' in dataframe.columns else 0,
                                  calculate_o3_index(row['o3']) if 'o3' in dataframe.columns else 0,
                                  calculate_pm2_5_index(row['pm2_5']) if 'pm2_5' in dataframe.columns else 0,
                                  calculate_pm10_index(row['pm10']) if 'pm10' in dataframe.columns else 0,
                                  calculate_so2_index(row['so2']) if 'so2' in dataframe.columns else 0)
        if row.get('aqi') is None else row['aqi'], axis=1)

    # drop_numerical_outliers(dataframe)

    dataframe = dataframe.dropna(axis='columns', how='all').dropna(axis='index', how='all')
    trim_dataframe(dataframe, 'time')
    if not dataframe.empty:
        dataframe.to_csv(collection_path, index=False)
