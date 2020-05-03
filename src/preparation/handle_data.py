import pandas as pd

from api.config import mongo


def trim_dataframe(dataframe):
    dataframe.drop_duplicates(inplace=True)
    dataframe.reset_index(drop=True, inplace=True)
    dataframe.sort_values(by='time', inplace=True)


def save_dataframe(dataframe, collection, path):
    db_records = pd.DataFrame(list(mongo.db[collection].find()))
    dataframe = dataframe[~dataframe['time'].isin(db_records['time'])]
    trim_dataframe(dataframe)
    dataframe_records = dataframe.to_dict('records')
    mongo.db[collection].insert_many(dataframe_records)

    dataframe = db_records.append(dataframe, ignore_index=True)
    trim_dataframe(dataframe)
    dataframe.to_csv(path, index=False)
