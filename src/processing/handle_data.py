from os import environ, path
from pickle import dump, HIGHEST_PROTOCOL, load
from typing import Optional

from pandas import DataFrame, read_csv

from api.config.database import mongo
from definitions import mongodb_connection
from .normalize_data import drop_unnecessary_features, trim_dataframe, rename_features


def convert_dtype(x: object) -> str:
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


def find_missing_data(new_dataframe: DataFrame, old_dataframe: DataFrame, column: str) -> DataFrame:
    dataframe = new_dataframe.loc[~new_dataframe['time'].isin(old_dataframe[column])].copy()
    return dataframe[dataframe.columns.intersection(old_dataframe.columns.values.tolist())]


def save_dataframe(dataframe: DataFrame, collection: str, collection_path: str, sensor_id: str) -> None:
    rename_features(dataframe)
    drop_unnecessary_features(dataframe)

    if (mongodb_env := environ.get(mongodb_connection)) is not None:
        db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id}, projection={'_id': False})))

        if len(db_records.index) > 0:
            dataframe = find_missing_data(dataframe, db_records, 'time')

    if len(dataframe.index) > 0:
        trim_dataframe(dataframe, 'time')
        dataframe.loc[:, 'sensorId'] = sensor_id
        if mongodb_env is not None:
            mongo.db[collection].insert_many(dataframe.to_dict('records'))

        if path.exists(collection_path):
            dataframe = find_missing_data(dataframe, read_csv(collection_path, engine='python'), 'time')
        dataframe.drop(columns='sensorId', inplace=True, errors='ignore')
        dataframe.to_csv(collection_path, header=not path.exists(collection_path), index=False, mode='a')


def store_dtypes(file_path: str, collection: str, dtypes: dict) -> None:
    with open(path.join(file_path, f'{collection}_dtypes.pkl'), 'wb') as out_file:
        dump(dtypes, out_file, HIGHEST_PROTOCOL)
