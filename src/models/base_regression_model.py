from os import path
from pickle import dump, HIGHEST_PROTOCOL, load


class BaseRegressionModel:
    def __init__(self, reg, param_grid: dict) -> None:
        self.reg = reg
        self.param_grid = param_grid

    async def get_params(self):
        return self.reg.get_params()

    async def set_params(self, **params) -> None:
        self.reg.set_params(**params)

    async def train(self, x, y) -> None:
        self.reg.fit(x, y)

    async def predict(self, x):
        return self.reg.predict(x)

    async def save(self, file_path: str) -> None:
        with open(path.join(file_path, f"{type(self).__name__}.mdl"), "wb") as out_file:
            dump(self.reg, out_file, HIGHEST_PROTOCOL)

    async def load(self, file_path: str) -> None:
        with open(path.join(file_path, f"{type(self).__name__}.mdl"), "rb") as in_file:
            self.reg = load(in_file)
