import numpy as np
import pandas as pd


def current_hour(t):
    return t.replace(microsecond=0, second=0, minute=0, hour=t.hour)


def normalize_pollution_data(df):
    dataframe = pd.DataFrame()
    dataframe_collection = {}

    for value in df['type'].unique():
        df_type = df[df['type'] == value].copy()
        df_type.rename(columns={'value': value}, inplace=True)
        df_type.drop(columns=['position', 'type'], inplace=True, errors='ignore')

        dataframe_collection[value] = df_type

    for key in dataframe_collection:
        if dataframe.empty:
            dataframe = dataframe.append(dataframe_collection[key], ignore_index=True)
        else:
            dataframe = pd.merge(dataframe, dataframe_collection[key], how='left', on='time')

    cols = list(dataframe)
    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index('time')))
    # use loc to reorder
    dataframe = dataframe.loc[:, cols]

    dataframe['time'] = pd.to_datetime(dataframe['time'], unit='s')
    dataframe['time'] = dataframe.apply(lambda row: current_hour(row['time']), axis=1)
    dataframe['time'] = dataframe['time'].values.astype(np.int64) // 10 ** 9

    return dataframe
