from sklearn.neural_network import MLPRegressor

from .base_regression_model import BaseRegressionModel


class MLPRegressionModel(BaseRegressionModel):
    def __init__(self) -> None:
        reg = MLPRegressor()
        param_grid = {
            "hidden_layer_sizes": [(50,), (100,), (50, 50), (100, 50)],  # Size of hidden layers
            "activation": ["relu", "tanh", "logistic"],  # Activation function for hidden layers
            "solver": ["adam", "sgd", "lbfgs"],  # Solver for weight optimization
            "alpha": [0.0001, 0.001, 0.01],  # L2 regularization parameter
            "learning_rate": ["constant", "adaptive"],  # Learning rate schedule
            "learning_rate_init": [0.001, 0.01, 0.1],  # Initial learning rate
            "max_iter": [200, 500, 1000],  # Maximum number of iterations
            "early_stopping": [True],
            # Whether to use early stopping to terminate training when the validation score doesn't improve
        }
        super().__init__(reg, param_grid)
