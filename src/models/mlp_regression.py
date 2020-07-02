from sklearn.neural_network import MLPRegressor

from .base_regression_model import BaseRegressionModel


class MLPRegressionModel(BaseRegressionModel):
    def __init__(self):
        reg = MLPRegressor()
        param_grid = {
            'hidden_layer_sizes': [i for i in range(1, 15)],
            'max_iter': [1000]
        }
        super().__init__(reg, param_grid)
