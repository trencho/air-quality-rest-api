from datetime import datetime, timedelta
from os import path

from numpy import abs
from pandas import concat, DataFrame, to_numeric
from scipy.stats import zscore
from sklearn.impute import KNNImputer

from api.config.logger import log
from definitions import DATA_PROCESSED_PATH, DATA_RAW_PATH, pollutants
from .calculate_index import calculate_aqi, calculate_co_index, calculate_no2_index, calculate_o3_index, \
    calculate_pm2_5_index, calculate_pm10_index, calculate_so2_index
from .handle_data import drop_unnecessary_features, find_missing_data, read_csv_in_chunks, rename_features, \
    trim_dataframe


def closest_hour(t: datetime) -> datetime:
    t = t if t.minute < 30 else t + timedelta(hours=1)
    return t.replace(minute=0, second=0, microsecond=0)


def current_hour() -> datetime:
    return datetime.now().replace(minute=0, second=0, microsecond=0)


def drop_numerical_outliers_with_iqr_score(dataframe: DataFrame, low: float = .05, high: float = .95) -> DataFrame:
    df = dataframe.loc[:, dataframe.columns != 'time']
    quant_df = df.quantile([low, high])
    df = df.apply(lambda x: x[(x > quant_df.loc[low, x.name]) & (x < quant_df.loc[high, x.name])], axis=0)
    df = concat([dataframe.loc[:, 'time'], df], axis=1)
    return df.dropna()


def drop_numerical_outliers_with_z_score(dataframe: DataFrame, z_thresh: int = 3) -> DataFrame:
    df = dataframe.loc[:, dataframe.columns != 'time']
    constrains = (abs(zscore(df)) < z_thresh).all(axis=1)
    df.drop(index=df.index[~constrains], inplace=True)
    df = concat([dataframe.loc[:, 'time'], df], axis=1)
    return df.dropna()


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
        dataframe = read_csv_in_chunks(path.join(DATA_RAW_PATH, city_name, sensor_id, f'{collection}.csv'))

        collection_path = path.join(DATA_PROCESSED_PATH, city_name, sensor_id, f'{collection}.csv')
        if path.exists(collection_path):
            dataframe = find_missing_data(dataframe, read_csv_in_chunks(collection_path), 'time')

        rename_features(dataframe)
        drop_unnecessary_features(dataframe)
        trim_dataframe(dataframe, 'time')
        if len(dataframe.index) == 0:
            return

        df_columns = dataframe.columns.copy()
        df_columns = df_columns.drop(['aqi', 'icon', 'precipType', 'summary'], errors='ignore')

        imp = KNNImputer()
        for column in df_columns:
            dataframe[column] = to_numeric(dataframe[column], errors='coerce')
            if dataframe[column].isna().all():
                dataframe.drop(columns=column, inplace=True, errors='ignore')
            if dataframe[column].isna().any():
                dataframe[column] = imp.fit_transform(dataframe[column].values.reshape(-1, 1))

        pollutants_wo_aqi = pollutants.copy()
        pollutants_wo_aqi.pop('aqi')
        columns = pollutants_wo_aqi.copy()
        for column in columns:
            if column not in dataframe.columns:
                pollutants_wo_aqi.pop(column)

        drop_columns_std = dataframe[list(pollutants_wo_aqi)].std()[
            dataframe[list(pollutants_wo_aqi)].std() == 0].index.values
        dataframe.drop(columns=drop_columns_std, inplace=True, errors='ignore')

        dataframe['aqi'] = dataframe.apply(
            lambda row: calculate_aqi(calculate_co_index(row['co']) if 'co' in dataframe.columns else 0,
                                      calculate_no2_index(row['no2']) if 'no2' in dataframe.columns else 0,
                                      calculate_o3_index(row['o3']) if 'o3' in dataframe.columns else 0,
                                      calculate_pm2_5_index(row['pm2_5']) if 'pm2_5' in dataframe.columns else 0,
                                      calculate_pm10_index(row['pm10']) if 'pm10' in dataframe.columns else 0,
                                      calculate_so2_index(row['so2']) if 'so2' in dataframe.columns else 0)
            if row.get('aqi') is None else row['aqi'], axis=1)

        # dataframe = drop_numerical_outliers_with_z_score(dataframe)

        if len(dataframe.index) > 0:
            dataframe.to_csv(collection_path, header=not path.exists(collection_path), index=False, mode='a')

    except Exception:
        log.error(f'Error occurred while processing {collection} data for {city_name} - {sensor_id}', exc_info=1)
