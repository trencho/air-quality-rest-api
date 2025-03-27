from os import cpu_count

from sklearn.linear_model import LinearRegression

from .base_regression_model import BaseRegressionModel


class LinearRegressionModel(BaseRegressionModel):
    def __init__(self) -> None:
        reg = LinearRegression()
        param_grid = {
            "fit_intercept": [True, False],  # Whether to calculate the intercept for this model
            "copy_X": [True, False],  # If True, X will be copied; else, it may be overwritten
            "n_jobs": [cpu_count() // 2]  # The number of jobs to use for the computation
        }
        super().__init__(reg, param_grid)
