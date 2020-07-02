from lightgbm import LGBMRegressor

from .base_regression_model import BaseRegressionModel


class LightGBMRegressionModel(BaseRegressionModel):
    def __init__(self):
        reg = LGBMRegressor()
        param_grid = {
            'num_leaves': (6, 50),
            'min_child_samples': (100, 500),
            'min_child_weight': [1e-5, 1e-3, 1e-2, 1e-1, 1, 1e1, 1e2, 1e3, 1e4],
            'subsample': (0.2, 0.8),
            'colsample_bytree': (0.4, 0.6),
            'reg_alpha': [0, 1e-1, 1, 2, 5, 7, 10, 50, 100],
            'reg_lambda': [0, 1e-1, 1, 5, 10, 20, 50, 100]
        }
        super().__init__(reg, param_grid)
