from os import path
from pickle import dump, HIGHEST_PROTOCOL, load


class BaseRegressionModel:
    def __init__(self, reg, param_grid):
        self.reg = reg
        self.param_grid = param_grid

    def get_params(self):
        return self.reg.get_params()

    def set_params(self, **params) -> None:
        self.reg.set_params(**params)

    def train(self, x, y) -> None:
        self.reg.fit(x, y)

    def predict(self, x):
        return self.reg.predict(x)

    def save(self, file_path: str) -> None:
        with open(path.join(file_path, type(self).__name__, f'{type(self).__name__}.pkl'), 'wb') as out_file:
            dump(self.reg, out_file, HIGHEST_PROTOCOL)

    def load(self, file_path: str) -> None:
        with open(path.join(file_path, type(self).__name__, f'{type(self).__name__}.pkl'), 'rb') as in_file:
            self.reg = load(in_file)
