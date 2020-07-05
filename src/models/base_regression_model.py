from os import path
from pickle import dump as pickle_dump, load as pickle_load, HIGHEST_PROTOCOL

from definitions import MODELS_PATH


class BaseRegressionModel:
    def __init__(self, reg, param_grid):
        self.reg = reg
        self.param_grid = param_grid

    def get_params(self):
        return self.reg.get_params()

    def set_params(self, **params):
        self.reg.set_params(**params)

    def train(self, X, y):
        self.reg.fit(X, y)

    def predict(self, X):
        y_pred = self.reg.predict(X)

        return y_pred

    def save(self, city_name, sensor_id, pollutant):
        with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, type(self).__name__,
                            type(self).__name__ + '.pkl'), 'wb') as out_file:
            pickle_dump(self.reg, out_file, HIGHEST_PROTOCOL)

    def load(self, city_name, sensor_id, pollutant):
        with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, type(self).__name__,
                            type(self).__name__ + '.pkl'), 'rb') as in_file:
            self.reg = pickle_load(in_file)