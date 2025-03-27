from pathlib import Path
from pickle import dumps, HIGHEST_PROTOCOL, load


class BaseRegressionModel:
    def __init__(self, reg, param_grid: dict) -> None:
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

    def save(self, model_path: Path) -> None:
        (model_path / f"{type(self).__name__}.mdl").write_bytes(dumps(self.reg, HIGHEST_PROTOCOL))

    def load(self, model_path: Path) -> None:
        with open(model_path / f"{type(self).__name__}.mdl", "rb") as in_file:
            self.reg = load(in_file)
