from os import cpu_count, path
from typing import override

from xgboost.sklearn import XGBRegressor

from .base_regression_model import BaseRegressionModel


class XGBoostRegressionModel(BaseRegressionModel):
    def __init__(self) -> None:
        reg = XGBRegressor()
        param_grid = {
            "max_depth": [3, 6, 9],  # Maximum depth of a tree
            "learning_rate": [0.01, 0.05, 0.1],  # Boosting learning rate
            "n_estimators": [100, 300, 500],  # Number of boosting rounds (trees)
            "n_jobs": [cpu_count() // 2],
            "subsample": [0.6, 0.8, 1.0],  # Subsample ratio of the training instance
            "colsample_bytree": [0.6, 0.8, 1.0],  # Subsample ratio of columns when constructing each tree
            "reg_alpha": [0.0, 0.1, 0.5],  # L1 regularization term on weights
            "reg_lambda": [0.0, 0.1, 0.5],  # L2 regularization term on weights
        }
        super().__init__(reg, param_grid)

    @override
    def save(self, model_path: str) -> None:
        self.reg.save_model(path.join(model_path, f"{type(self).__name__}.mdl"))

    @override
    def load(self, model_path: str) -> None:
        self.reg.load_model(path.join(model_path, f"{type(self).__name__}.mdl"))
