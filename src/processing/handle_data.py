from os import environ, path
from pickle import dump, HIGHEST_PROTOCOL, load
from typing import Optional

from pandas import concat, DataFrame, read_csv, to_datetime

from api.config.database import mongo
from definitions import chunk_size, mongodb_connection
from .normalize_data import drop_unnecessary_features, find_missing_data, trim_dataframe, rename_features


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


def read_csv_in_chunks(data_path: str, index_col: str = None) -> Optional[DataFrame]:
    chunks = []
    for chunk in read_csv(data_path, index_col=index_col, chunksize=chunk_size):
        chunk.index = to_datetime(chunk.index, unit='s')
        if len(chunk.index) > 0:
            chunks.append(chunk)

    return concat(chunks) if len(chunks) > 0 else None


def save_dataframe(dataframe: DataFrame, collection: str, collection_path: str, sensor_id: str) -> None:
    rename_features(dataframe)
    drop_unnecessary_features(dataframe)

    if (mongodb_env := environ.get(mongodb_connection)) is not None:
        db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id}, projection={'_id': False})))

        if len(db_records.index) > 0:
            dataframe = find_missing_data(dataframe, db_records, 'time')

    trim_dataframe(dataframe, 'time')
    if len(dataframe.index) > 0:
        dataframe.loc[:, 'sensorId'] = sensor_id
        if mongodb_env is not None:
            mongo.db[collection].insert_many(dataframe.to_dict('records'))

        if (df := read_csv_in_chunks(collection_path)) is not None:
            dataframe = find_missing_data(dataframe, df, 'time')
        dataframe.drop(columns='sensorId', inplace=True, errors='ignore')
        dataframe.to_csv(collection_path, header=not path.exists(collection_path), index=False, mode='a')


def store_dtypes(file_path: str, collection: str, dtypes: dict) -> None:
    with open(path.join(file_path, f'{collection}_dtypes.pkl'), 'wb') as out_file:
        dump(dtypes, out_file, HIGHEST_PROTOCOL)
