from os import environ, path
from typing import Optional

from pandas import DataFrame, read_csv

from api.config.database import mongo
from definitions import mongodb_connection


def save_dataframe(dataframe: DataFrame, collection: str, collection_path: Optional[str], sensor_id: str) -> None:
    if environ.get(mongodb_connection) is not None:
        db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id}, projection={'_id': False})))

        if not db_records.empty:
            dataframe = dataframe.loc[~dataframe['time'].isin(db_records['time'])].copy()

    trim_dataframe(dataframe, 'time')
    if not dataframe.empty:
        dataframe.loc[:, 'sensorId'] = sensor_id
        mongo.db[collection].insert_many(dataframe.to_dict('records'))

        if path.exists(collection_path):
            dataframe = dataframe.append(read_csv(collection_path), ignore_index=True)
            trim_dataframe(dataframe, 'time')
        dataframe.drop(columns='sensorId', inplace=True, errors='ignore')
        dataframe.to_csv(collection_path, index=False)


def trim_dataframe(dataframe: DataFrame, column: str) -> None:
    dataframe.drop_duplicates(subset=column, keep='last', inplace=True)
    dataframe.reset_index(drop=True, inplace=True)
    dataframe.sort_values(by=column, inplace=True)
