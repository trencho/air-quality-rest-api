import os

import pandas as pd

from api.config import mongo
from definitions import DATA_EXTERNAL_PATH


def create_data_paths(city_name, sensor_id):
    if not os.path.exists(
            DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor_id + '/'):
        os.makedirs(DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor_id + '/')


def save_dataframe(df, collection, path):
    if os.path.exists(path):
        dataframe = pd.read_csv(path)
        dataframe.append(df, ignore_index=True, sort=True)
        dataframe.to_csv(path, index=False)
    else:
        dataframe = df
        dataframe.to_csv(path, index=False)

    dataframe.reset_index(inplace=True)
    dataframe_records = dataframe.to_dict('records')
    mongo.db[collection].insert_many(dataframe_records)
