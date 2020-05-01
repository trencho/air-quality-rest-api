import os

import pandas as pd

from api.config import mongo
from .pollution_data import extract_pollution_json
from .weather_data import extract_weather_json


def save_dataframe(df, collection, path):
    if os.path.exists(path):
        dataframe = pd.read_csv(path)
        dataframe.append(df, ignore_index=True, sort=True)
        dataframe.to_csv(path, index=False)
    else:
        dataframe = df
        dataframe.to_csv(path, index=False)

    dataframe_records = dataframe.T.to_json()
    mongo.air_quality[collection].insert_many(dataframe_records)
