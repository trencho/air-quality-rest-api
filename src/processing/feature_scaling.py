import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


def min_max_scaling(dataframe):
    dataframe_columns = dataframe.columns
    dataframe = MinMaxScaler().fit_transform(dataframe)

    return pd.DataFrame(dataframe, columns=dataframe_columns)


def robust_scaling(dataframe):
    dataframe_columns = dataframe.columns
    dataframe = RobustScaler().fit_transform(dataframe)

    return pd.DataFrame(dataframe, columns=dataframe_columns)


def standard_scaling(dataframe):
    dataframe_columns = dataframe.columns
    dataframe = StandardScaler().fit_transform(dataframe)

    return pd.DataFrame(dataframe, columns=dataframe_columns)
