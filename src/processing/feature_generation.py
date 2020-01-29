import numpy as np
import pandas as pd


def generate_features(dataset, pollutant):
    dataframe = dataset.copy()
    dataframe['sinTime'] = np.sin(dataframe['time'])
    dataframe['cosTime'] = np.cos(dataframe['time'])

    dataframe['prevValue'] = dataframe[pollutant].shift(1)
    dataframe['prevValue'].interpolate(method='nearest', fill_value='extrapolate', inplace=True)

    dataframe['dayOfWeek'] = dataframe['time'].apply(lambda x: pd.to_datetime(x).weekday())
    dataframe['isWeekend'] = dataframe['time'].apply(
        lambda x: 1 if pd.to_datetime(x).weekday() in (5, 6) else 0)

    dataframe.fillna(method='bfill', inplace=True)
    dataframe.fillna(method='ffill', inplace=True)

    dataframe['icon'] = pd.Categorical(dataframe['icon'])
    dataframe['precipType'] = pd.Categorical(dataframe['precipType'])
    dataframe['summary'] = pd.Categorical(dataframe['summary'])

    dataframe = pd.get_dummies(dataframe, drop_first=True)

    return dataframe
