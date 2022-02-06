from math import isinf, isnan
from os import path
from typing import Optional

from numpy import abs, array, mean, ndarray, sqrt
from pandas import DataFrame, Series
from sklearn.metrics import mean_absolute_error, mean_squared_error

from definitions import RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH


def mean_absolute_percentage_error(y_true: Series, y_predicted: Series) -> Optional[ndarray]:
    y_true, y_predicted = array(y_true), array(y_predicted)
    mape = mean(abs((y_true - y_predicted) / y_true)) * 100
    return None if isinf(mape) or isnan(mape) else mape


def save_errors(city_name: str, sensor_id: str, pollutant: str, model_name: str, y_true: Series,
                y_predicted: Series) -> [float, ndarray]:
    mae = mean_absolute_error(y_true, y_predicted)
    dataframe = DataFrame({
        'Mean Absolute Error': [mae],
        'Mean Absolute Percentage Error': [mean_absolute_percentage_error(y_true, y_predicted)],
        'Mean Squared Error': [mean_squared_error(y_true, y_predicted)],
        'Root Mean Squared Error': [sqrt(mean_squared_error(y_true, y_predicted))]
    }, columns=['Mean Absolute Error', 'Mean Absolute Percentage Error', 'Mean Squared Error',
                'Root Mean Squared Error'])
    dataframe.to_csv(path.join(RESULTS_ERRORS_PATH, 'data', city_name, sensor_id, pollutant, model_name, 'error.csv'),
                     index=False)

    return mae


def save_results(city_name: str, sensor_id: str, pollutant: str, model_name: str, dataframe: DataFrame) -> None:
    dataframe.to_csv(
        path.join(RESULTS_PREDICTIONS_PATH, 'data', city_name, sensor_id, pollutant, model_name, 'prediction.csv'))
