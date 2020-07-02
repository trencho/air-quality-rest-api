from sklearn.svm import SVR

from .base_regression_model import BaseRegressionModel


class SupportVectorRegressionModel(BaseRegressionModel):
    def __init__(self):
        reg = SVR()
        param_grid = {
            'gamma': [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 0.01, 0.1, 0.2, 0.5, 0.6, 0.9],
            'C': [1, 10, 100, 1000, 10000]
        }
        super().__init__(reg, param_grid)
