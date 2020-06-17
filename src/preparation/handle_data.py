from pandas import DataFrame
from pymongo import ASCENDING

from api.config.db import mongo


def trim_dataframe(dataframe):
    dataframe.drop_duplicates(inplace=True)
    dataframe.reset_index(drop=True, inplace=True)
    dataframe.sort_values(by='time', inplace=True)


def save_dataframe(dataframe, collection, path, sensor_id):
    db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id})))
    db_records.drop(columns='_id', inplace=True, errors='ignore')

    if not db_records.empty:
        dataframe = dataframe.merge(db_records, how='outer', on='time',
                                    indicator=True).loc[lambda x: x['_merge'] == 'left_only']

    dataframe.drop(columns='_merge', inplace=True, errors='ignore')
    trim_dataframe(dataframe)
    if not dataframe.empty:
        dataframe['sensorId'] = sensor_id
        dataframe_records = dataframe.to_dict('records')
        mongo.db[collection].insert_many(dataframe_records)
        mongo.db[collection].find().sort('time', ASCENDING)

        dataframe = dataframe.append(db_records, ignore_index=True)
        dataframe.drop(columns='sensorId', inplace=True, errors='ignore')
        trim_dataframe(dataframe)
        dataframe.to_csv(path, index=False)
