import pandas as pd

from api.config.db import mongo


def trim_dataframe(dataframe):
    dataframe.drop_duplicates(inplace=True)
    dataframe.reset_index(drop=True, inplace=True)
    dataframe.sort_values(by='time', inplace=True)


def save_dataframe(dataframe, collection, path, sensor_id):
    db_records = pd.DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id})))
    db_records.drop('_id', axis=1, inplace=True, errors='ignore')

    if not db_records.empty:
        dataframe = dataframe.merge(db_records, how='outer', on=['sensorId', 'time'],
                                    indicator=True).loc[lambda x: x['_merge'] == 'left_only']
    dataframe.drop('_merge', axis=1, inplace=True, errors='ignore')
    trim_dataframe(dataframe)
    if not dataframe.empty:
        dataframe_records = dataframe.to_dict('records')
        mongo.db[collection].insert_many(dataframe_records)

        dataframe = dataframe.append(db_records, ignore_index=True)
        trim_dataframe(dataframe)
        dataframe.to_csv(path, index=False)
