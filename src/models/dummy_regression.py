from sklearn.dummy import DummyRegressor

from .base_regression_model import BaseRegressionModel


class DummyRegressionModel(BaseRegressionModel):
    def __init__(self):
        reg = DummyRegressor()
        param_grid = {
            'strategy': ['mean', 'median', 'quantile'],
            'quantile': [0.0, 0.5, 1.0]
        }
        super().__init__(reg, param_grid)
