import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


def value_scaling(dataframe, scale='robust'):
    if scale == 'min_max':
        scaler = MinMaxScaler()
    elif scale == 'robust':
        scaler = RobustScaler()
    elif scale == 'standard':
        scaler = StandardScaler()

    dataframe_columns = dataframe.columns
    dataframe = scaler.fit_transform(dataframe)

    return pd.DataFrame(dataframe, columns=dataframe_columns)
