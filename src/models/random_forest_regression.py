from os import cpu_count

from sklearn.ensemble import RandomForestRegressor

from .base_regression_model import BaseRegressionModel


class RandomForestRegressionModel(BaseRegressionModel):
    def __init__(self) -> None:
        reg = RandomForestRegressor()
        param_grid = {
            "n_estimators": [100, 300, 500],  # Number of trees in the forest
            "max_depth": [None, 10, 20],  # Maximum depth of the trees
            "min_samples_split": [2, 5, 10],  # Minimum number of samples required to split an internal node
            "min_samples_leaf": [1, 2, 4],  # Minimum number of samples required to be at a leaf node
            "max_features": [None, "sqrt", "log2"],  # Number of features to consider when looking for the best split
            "n_jobs": [cpu_count() // 2]  # Number of jobs to run in parallel
        }
        super().__init__(reg, param_grid)
