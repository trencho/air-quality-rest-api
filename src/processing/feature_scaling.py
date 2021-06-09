from traceback import format_exc

from pandas import DataFrame
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


def value_scaling(dataframe, scale='robust'):
    if scale == 'min_max':
        scaler = MinMaxScaler()
    elif scale == 'standard':
        scaler = StandardScaler()
    else:
        scaler = RobustScaler()

    dataframe_index = dataframe.index
    dataframe_columns = dataframe.columns
    try:
        dataframe = scaler.fit_transform(dataframe)
    except ValueError:
        print(format_exc())

    return DataFrame(dataframe, dataframe_index, dataframe_columns)
