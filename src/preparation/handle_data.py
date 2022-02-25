from os import environ, path
from pickle import dump, HIGHEST_PROTOCOL, load
from typing import Optional

from numpy import nan
from pandas import concat, DataFrame, read_csv

from api.config.database import mongo
from definitions import mongodb_connection


def convert_dtype(x):
    if not x:
        return ''
    try:
        return str(x)
    except Exception:
        return ''


def find_dtypes(file_path: str, collection: str) -> Optional[dict]:
    dtypes_path = path.join(file_path, f'{collection}_dtypes.pkl')
    if path.exists(dtypes_path):
        with open(dtypes_path, 'rb') as in_file:
            return load(in_file)

    return None


def save_dataframe(dataframe: DataFrame, collection: str, collection_path: str, sensor_id: str) -> None:
    if (mongodb_env := environ.get(mongodb_connection)) is not None:
        db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id}, projection={'_id': False})))

        if len(db_records.index) > 0:
            dataframe = dataframe.loc[~dataframe['time'].isin(db_records['time'])].copy()
            dataframe = dataframe[dataframe.columns.intersection(db_records.columns.values.tolist())]

    if len(dataframe.index) > 0:
        trim_dataframe(dataframe, 'time')
        dataframe.loc[:, 'sensorId'] = sensor_id
        if mongodb_env is not None:
            mongo.db[collection].insert_many(dataframe.to_dict('records'))

        if path.exists(collection_path):
            dataframe = concat([dataframe, read_csv(collection_path, engine='python')], ignore_index=True)
            trim_dataframe(dataframe, 'time')
        dataframe.drop(columns='sensorId', inplace=True, errors='ignore')
        dataframe.to_csv(collection_path, index=False)


def store_dtypes(file_path: str, collection: str, dtypes: dict) -> None:
    with open(path.join(file_path, f'{collection}_dtypes.pkl'), 'wb') as out_file:
        dump(dtypes, out_file, HIGHEST_PROTOCOL)


def trim_dataframe(dataframe: DataFrame, column: str) -> None:
    dataframe.replace(to_replace=0, value=nan, inplace=True)
    dataframe.dropna(axis='columns', how='all', inplace=True)
    dataframe.drop_duplicates(subset=column, keep='last', inplace=True)
    dataframe.reset_index(drop=True, inplace=True)
    dataframe.sort_values(by=column, inplace=True)
