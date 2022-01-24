from os import environ, path

from numpy import nan
from pandas import concat, DataFrame, read_csv

from api.config.database import mongo
from definitions import mongodb_connection


def save_dataframe(dataframe: DataFrame, collection: str, collection_path: str, sensor_id: str) -> None:
    if (mongodb_env := environ.get(mongodb_connection)) is not None:
        db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id}, projection={'_id': False})))

        if len(db_records.index) > 0:
            dataframe = dataframe.loc[~dataframe['time'].isin(db_records['time'])].copy()

    if len(dataframe.index) > 0:
        trim_dataframe(dataframe, 'time')
        dataframe.loc[:, 'sensorId'] = sensor_id
        if mongodb_env is not None:
            mongo.db[collection].insert_many(dataframe.to_dict('records'))

        if path.exists(collection_path):
            dataframe = concat([dataframe, read_csv(collection_path)], ignore_index=True)
            trim_dataframe(dataframe, 'time')
        dataframe.drop(columns='sensorId', inplace=True, errors='ignore')
        dataframe.to_csv(collection_path, index=False)


def trim_dataframe(dataframe: DataFrame, column: str) -> None:
    df = dataframe.replace(0, nan)
    dataframe.drop(columns=df.columns[df.isna().all()].tolist(), inplace=True, errors='ignore')
    dataframe.drop_duplicates(subset=column, keep='last', inplace=True)
    dataframe.reset_index(drop=True, inplace=True)
    dataframe.sort_values(by=column, inplace=True)
