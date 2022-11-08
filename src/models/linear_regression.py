from os import cpu_count

from sklearn.linear_model import LinearRegression

from .base_regression_model import BaseRegressionModel


class LinearRegressionModel(BaseRegressionModel):
    def __init__(self) -> None:
        reg = LinearRegression()
        param_grid = {
            "fit_intercept": [True, False],
            "copy_X": [True, False],
            "n_jobs": [cpu_count() // 2]
        }
        super().__init__(reg, param_grid)
