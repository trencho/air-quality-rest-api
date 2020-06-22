from os import path
from pickle import dump as pickle_dump, load as pickle_load, HIGHEST_PROTOCOL

from sklearn.svm import SVR

from definitions import MODELS_PATH


class SupportVectorRegressionModel:
    def __init__(self):
        self.reg = SVR()
        self.param_grid = {
            'gamma': [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 0.01, 0.1, 0.2, 0.5, 0.6, 0.9],
            'C': [1, 10, 100, 1000, 10000]
        }

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
