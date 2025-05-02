from logging import getLogger
from math import isinf
from typing import Optional

from numpy import abs, inf, mean, nan, ndarray, sqrt
from pandas import DataFrame, Series
from sklearn.metrics import mean_absolute_error, mean_squared_error

from definitions import RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH

logger = getLogger(__name__)


def filter_invalid_values(
        y_true: [ndarray, Series], y_predicted: [ndarray, Series]
) -> tuple:
    dataframe = (
        DataFrame({"y_true": y_true, "y_predicted": y_predicted})
        .replace([-inf, inf], nan)
        .dropna()
    )
    return dataframe["y_true"].values, dataframe["y_predicted"].values


def mean_absolute_percentage_error(
        y_true: ndarray, y_predicted: ndarray
) -> Optional[float]:
    mape = mean(abs((y_true - y_predicted) / y_true)) * 100
    return None if isinf(mape) else mape


def save_errors(model_path: str, y_true: ndarray, y_predicted: ndarray) -> float:
    y_true, y_predicted = filter_invalid_values(y_true, y_predicted)
    try:
        mae = mean_absolute_error(y_true, y_predicted)
        mse = mean_squared_error(y_true, y_predicted)
        dataframe = DataFrame(
            {
                "Mean Absolute Error": [None if isinf(mae) else mae],
                "Mean Absolute Percentage Error": [
                    mean_absolute_percentage_error(y_true, y_predicted)
                ],
                "Mean Squared Error": [mse],
                "Root Mean Squared Error": [sqrt(mse)],
            }
        )
        dataframe.to_csv(
            RESULTS_ERRORS_PATH / "data" / model_path / "error.csv", index=False
        )

        return mae
    except (ValueError, IOError):
        logger.error("Error saving errors", exc_info=True)
        return inf


def save_results(model_path: str, dataframe: DataFrame) -> None:
    dataframe.to_csv(RESULTS_PREDICTIONS_PATH / "data" / model_path / "prediction.csv")
