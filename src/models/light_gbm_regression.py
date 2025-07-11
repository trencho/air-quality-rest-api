from os import cpu_count
from pathlib import Path
from typing import override

from lightgbm import Booster, LGBMRegressor

from .base_regression_model import BaseRegressionModel


class LightGBMRegressionModel(BaseRegressionModel):
    def __init__(self) -> None:
        reg = LGBMRegressor()
        param_grid = {
            "boosting": ["gbdt", "dart", "goss"],  # Booster type
            "num_iterations": [100, 500, 1000],  # Number of boosted trees to fit
            "learning_rate": [0.01, 0.05, 0.1],  # Boosting learning rate
            "num_leaves": [20, 30, 40, 50],  # Maximum tree leaves for base learners
            "num_threads": [cpu_count() // 2],  # Number of threads for LightGBM
            "max_depth": [
                -1,
                5,
                10,
                15,
            ],  # Maximum tree depth for base learners, -1 means no limit
            "min_data_in_leaf": [
                20,
                30,
                40,
                50,
            ],  # Minimum number of data needed in a child (leaf)
            "bagging_fraction": [
                0.6,
                0.8,
                1.0,
            ],  # Subsample ratio of the training instance
            "feature_fraction": [
                0.6,
                0.8,
                1.0,
            ],  # Subsample ratio of columns when constructing each tree
            "lambda_l1": [0.0, 0.1, 0.5],  # L1 regularization term on weights
            "lambda_l2": [0.0, 0.1, 0.5],  # L2 regularization term on weights
            "min_gain_to_split": [0.0, 0.1, 0.2],
            # Minimum loss reduction required to make a further partition on a leaf node of the tree
            "verbosity": [-1],  # Verbosity of printing messages
            "bin_construct_sample_cnt": [
                10000,
                20000,
            ],  # Number of samples for constructing bins
        }
        super().__init__(reg, param_grid)

    @override
    def save(self, model_path: str) -> None:
        self.reg.booster_.save_model(Path(model_path) / f"{type(self).__name__}.mdl")

    @override
    def load(self, model_path: str) -> None:
        self.reg._Booster = Booster(
            model_file=Path(model_path) / f"{type(self).__name__}.mdl"
        )
