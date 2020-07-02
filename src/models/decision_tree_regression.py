from sklearn.tree import DecisionTreeRegressor

from .base_regression_model import BaseRegressionModel


class DecisionTreeRegressionModel(BaseRegressionModel):
    def __init__(self):
        reg = DecisionTreeRegressor()
        param_grid = {
            'criterion': ['mse', 'mae'],
            'max_depth': [2, 6, 8],
            'min_samples_split': [10, 20, 40],
            'min_samples_leaf': [20, 40, 100],
            'max_leaf_nodes': [5, 20, 100]
        }
        super().__init__(reg, param_grid)
