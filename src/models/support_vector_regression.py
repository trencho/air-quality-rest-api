from sklearn.svm import SVR

from .base_regression_model import BaseRegressionModel


class SupportVectorRegressionModel(BaseRegressionModel):
    def __init__(self):
        reg = SVR()
        param_grid = {
            "kernel": ["linear", "rbf", "poly"],  # Kernel function
            "C": [0.1, 1, 10, 100],  # Regularization parameter
            "epsilon": [
                0.1,
                0.2,
                0.3,
            ],  # Epsilon parameter in the epsilon-insensitive loss function
        }
        super().__init__(reg, param_grid)
