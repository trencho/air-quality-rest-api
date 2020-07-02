from sklearn.linear_model import LinearRegression

from .base_regression_model import BaseRegressionModel


class LinearRegressionModel(BaseRegressionModel):
    def __init__(self):
        reg = LinearRegression()
        param_grid = {
            'fit_intercept': [True, False],
            'normalize': [True, False],
            'copy_X': [True, False]
        }
        super().__init__(reg, param_grid)
