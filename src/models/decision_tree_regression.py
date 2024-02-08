from sklearn.tree import DecisionTreeRegressor

from .base_regression_model import BaseRegressionModel


class DecisionTreeRegressionModel(BaseRegressionModel):
    def __init__(self) -> None:
        reg = DecisionTreeRegressor()
        param_grid = {
            "criterion": ["absolute_error", "squared_error"],
            "max_depth": [5, 10, 15, None],
            "min_samples_split": [2, 5, 10, 20],
            "min_samples_leaf": [1, 2, 5, 10],
            "max_features": ["auto", "sqrt", "log2", None],
            "max_leaf_nodes": [5, 20, 100]
        }
        super().__init__(reg, param_grid)
