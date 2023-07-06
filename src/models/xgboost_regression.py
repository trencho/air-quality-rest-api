from os import cpu_count, path

from xgboost.sklearn import XGBRegressor

from .base_regression_model import BaseRegressionModel


class XGBoostRegressionModel(BaseRegressionModel):
    def __init__(self) -> None:
        reg = XGBRegressor()
        param_grid = {
            "n_jobs": [cpu_count() // 2],
            "learning_rate": [.03, 0.05, .07],
            "max_depth": [5, 6, 7],
            "min_child_weight": [4],
            "subsample": [0.7],
            "colsample_bytree": [0.7],
            "n_estimators": [500]
        }
        super().__init__(reg, param_grid)

    def save(self, file_path: str) -> None:
        self.reg.save_model(path.join(file_path, f"{type(self).__name__}.mdl"))

    def load(self, file_path: str) -> None:
        self.reg.load_model(path.join(file_path, f"{type(self).__name__}.mdl"))
