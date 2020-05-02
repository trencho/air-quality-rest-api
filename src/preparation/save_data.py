import os

import pandas as pd

from api.config.db import mongo


def save_dataframe(df, collection, path):
    if os.path.exists(path):
        dataframe = pd.read_csv(path)
        dataframe.append(df, ignore_index=True, sort=True)
        dataframe.to_csv(path, index=False)
    else:
        dataframe = df
        dataframe.to_csv(path, index=False)

    dataframe_records = dataframe.T.to_json()
    mongo.db[collection].insert_many(dataframe_records)
