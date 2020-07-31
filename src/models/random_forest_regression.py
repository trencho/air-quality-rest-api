from numpy import linspace
from sklearn.ensemble import RandomForestRegressor

from .base_regression_model import BaseRegressionModel


class RandomForestRegressionModel(BaseRegressionModel):
    def __init__(self):
        reg = RandomForestRegressor()
        max_depth = [int(x) for x in linspace(10, 110, num=11)]
        max_depth.append(None)
        param_grid = {
            'n_estimators': [int(x) for x in linspace(start=200, stop=2000, num=10)],
            'max_depth': max_depth,
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['auto', 'sqrt'],
            'bootstrap': [True, False]
        }
        super().__init__(reg, param_grid)
