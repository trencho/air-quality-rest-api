from pandas import DataFrame
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


def value_scaling(dataframe, scale='robust'):
    if scale == 'min_max':
        scaler = MinMaxScaler()
    elif scale == 'standard':
        scaler = StandardScaler()
    elif scale == 'robust':
        scaler = RobustScaler()
    else:
        raise ValueError(scale + ' is not a valid scaler')

    dataframe_columns = dataframe.columns
    dataframe = scaler.fit_transform(dataframe)

    return DataFrame(dataframe, columns=dataframe_columns)
