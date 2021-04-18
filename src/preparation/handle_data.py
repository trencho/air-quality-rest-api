from os import environ, path

from pandas import DataFrame, read_csv

from api.config.database import mongo
from definitions import mongodb_connection


def trim_dataframe(dataframe, column):
    dataframe.drop_duplicates(subset=column, keep='last', inplace=True)
    dataframe.reset_index(drop=True, inplace=True)
    dataframe.sort_values(by=column, inplace=True)


def save_dataframe(dataframe, collection, collection_path, sensor_id):
    if environ.get(mongodb_connection) is not None:
        db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id}, projection={'_id': False})))

        if not db_records.empty:
            dataframe = dataframe.merge(db_records, how='left', on='time',
                                        indicator=True).query('_merge == "left_only"').drop(columns='_merge')

    trim_dataframe(dataframe, 'time')
    if not dataframe.empty:
        dataframe['sensorId'] = sensor_id
        mongo.db[collection].insert_many(dataframe.to_dict('records'))

        if path.exists(collection_path):
            dataframe = dataframe.append(read_csv(collection_path), ignore_index=True)
        dataframe.drop(columns='sensorId', inplace=True, errors='ignore')
        trim_dataframe(dataframe, 'time')
        dataframe.to_csv(collection_path, index=False)
