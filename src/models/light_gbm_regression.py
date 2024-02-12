from os import cpu_count, path
from typing import override

from lightgbm import Booster, LGBMRegressor

from .base_regression_model import BaseRegressionModel


class LightGBMRegressionModel(BaseRegressionModel):
    def __init__(self) -> None:
        reg = LGBMRegressor()
        param_grid = {
            "boosting_type": ["gbdt", "dart", "goss"],
            "num_leaves": [20, 30, 40, 50],  # Maximum tree leaves for base learners
            "max_depth": [-1, 5, 10, 15],  # Maximum tree depth for base learners, -1 means no limit
            "learning_rate": [0.01, 0.05, 0.1],  # Boosting learning rate
            "n_estimators": [50, 100, 200],  # Number of boosted trees to fit
            "subsample_for_bin": [20000, 30000, 40000],  # Number of samples for constructing bins
            "min_split_gain": [0.0, 0.1, 0.2],
            # Minimum loss reduction required to make a further partition on a leaf node of the tree
            "min_child_samples": [20, 30, 40, 50],  # Minimum number of data needed in a child (leaf)
            "subsample": [0.6, 0.8, 1.0],  # Subsample ratio of the training instance
            "colsample_bytree": [0.6, 0.8, 1.0],  # Subsample ratio of columns when constructing each tree
            "reg_alpha": [0.0, 0.1, 0.5],  # L1 regularization term on weights
            "reg_lambda": [0.0, 0.1, 0.5],  # L2 regularization term on weights
            "n_jobs": [cpu_count() // 2]
        }
        super().__init__(reg, param_grid)

    @override
    def save(self, model_path: str) -> None:
        self.reg.booster_.save_model(path.join(model_path, f"{type(self).__name__}.mdl"))

    @override
    def load(self, model_path: str) -> None:
        self.reg._Booster = Booster(model_file=path.join(model_path, f"{type(self).__name__}.mdl"))
