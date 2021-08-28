from pandas import DataFrame
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


def value_scaling(dataframe: DataFrame, scale: str = 'robust') -> DataFrame:
    if scale == 'min_max':
        scaler = MinMaxScaler()
    elif scale == 'standard':
        scaler = StandardScaler()
    else:
        scaler = RobustScaler()

    dataframe_index = dataframe.index
    dataframe_columns = dataframe.columns
    dataframe = scaler.fit_transform(dataframe)

    return DataFrame(dataframe, dataframe_index, dataframe_columns)
