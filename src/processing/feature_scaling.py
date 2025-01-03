from pandas import DataFrame
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

# Constants for scaler types
SCALER_TYPES = {
    "min_max": MinMaxScaler(),
    "standard": StandardScaler(),
    "robust": RobustScaler()
}


def value_scaling(dataframe: DataFrame, scale: str = "robust") -> DataFrame:
    scaler = SCALER_TYPES.get(scale, RobustScaler())
    dataframe_index = dataframe.index
    dataframe_columns = dataframe.columns
    dataframe = scaler.fit_transform(dataframe)
    return DataFrame(dataframe, dataframe_index, dataframe_columns)
