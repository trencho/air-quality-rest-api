from os import cpu_count

from xgboost.sklearn import XGBRegressor

from .base_regression_model import BaseRegressionModel


class XGBoostRegressionModel(BaseRegressionModel):
    def __init__(self):
        reg = XGBRegressor()
        param_grid = {
            'n_jobs': [cpu_count() // 2],
            'learning_rate': [.03, 0.05, .07],
            'max_depth': [5, 6, 7],
            'min_child_weight': [4],
            'subsample': [0.7],
            'colsample_bytree': [0.7],
            'n_estimators': [500]
        }
        super().__init__(reg, param_grid)
