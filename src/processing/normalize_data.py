from datetime import datetime, timedelta
from os import path

from numpy import abs, nan
from pandas import concat, DataFrame, read_csv, to_numeric
from scipy.stats import zscore
from sklearn.impute import KNNImputer

from api.config.logger import log
from definitions import DATA_PROCESSED_PATH, DATA_RAW_PATH, pollutants
from .calculate_index import calculate_aqi, calculate_co_index, calculate_no2_index, calculate_o3_index, \
    calculate_pm2_5_index, calculate_pm10_index, calculate_so2_index


def closest_hour(t: datetime) -> datetime:
    t = t if t.minute < 30 else t + timedelta(hours=1)
    return t.replace(minute=0, second=0, microsecond=0)


def current_hour() -> datetime:
    return datetime.now().replace(minute=0, second=0, microsecond=0)


def drop_numerical_outliers(dataframe: DataFrame, z_thresh: int = 3) -> None:
    constrains = (abs(zscore(dataframe)) < z_thresh).all(axis=1)
    dataframe.drop(index=dataframe.index[~constrains], inplace=True)


def drop_unnecessary_features(dataframe: DataFrame) -> None:
    dataframe.drop(columns=dataframe.filter(regex='weather').columns, axis=1, inplace=True)
    dataframe.drop(columns=['precipProbability', 'precipType', 'ozone', 'co2'], inplace=True, errors='ignore')


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
    return t.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def process_data(city_name: str, sensor_id: str, collection: str) -> None:
    try:
        dataframe = read_csv(path.join(DATA_RAW_PATH, city_name, sensor_id, f'{collection}.csv'), engine='python')

        collection_path = path.join(DATA_PROCESSED_PATH, city_name, sensor_id, f'{collection}.csv')
        if path.exists(collection_path):
            dataframe = concat([dataframe, read_csv(collection_path, engine='python')], ignore_index=True)

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

        drop_columns_std = dataframe[list(pollutants_wo_aqi)].std()[
            dataframe[list(pollutants_wo_aqi)].std() == 0].index.values

        dataframe[list(pollutants_wo_aqi)].replace(0, nan).bfill(inplace=True)
        dataframe[list(pollutants_wo_aqi)].replace(0, nan).ffill(inplace=True)
        dataframe.drop(columns=drop_columns_std, inplace=True, errors='ignore')

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
        if len(dataframe.index) > 0:
            rename_features(dataframe)
            drop_unnecessary_features(dataframe)
            dataframe.to_csv(collection_path, index=False)

    except Exception:
        log.error(f'Error occurred while processing data for {city_name} - {sensor_id}', exc_info=1)


def rename_features(dataframe: DataFrame) -> None:
    dataframe.rename(
        columns={'dt': 'time', 'temperature': 'temp', 'apparentTemperature': 'feels_like', 'dewPoint': 'dew_point',
                 'cloudCover': 'clouds', 'windSpeed': 'wind_speed', 'windGust': 'wind_gust', 'windBearing': 'wind_deg',
                 'summary': 'weather.description', 'icon': 'weather.icon', 'uvIndex': 'uvi',
                 'precipIntensity': 'precipitation', 'AQI': 'aqi', 'CO': 'co', 'CO2': 'co2', 'NH3': 'nh3', 'NO': 'no',
                 'NO2': 'no2', 'O3': 'o3', 'PM25': 'pm2_5', 'PM10': 'pm10', 'SO2': 'so2'}, inplace=True,
        errors='ignore')


def trim_dataframe(dataframe: DataFrame, column: str) -> None:
    dataframe.replace(to_replace=0, value=nan, inplace=True)
    dataframe.dropna(axis='columns', how='all', inplace=True)
    dataframe.drop_duplicates(subset=column, keep='last', inplace=True)
    dataframe.reset_index(drop=True, inplace=True)
    dataframe.sort_values(by=column, inplace=True)
