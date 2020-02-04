import pickle

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from definitions import MODELS_PATH


class RandomForestRegressionModel:
    def __init__(self):
        max_depth = [int(x) for x in np.linspace(10, 110, num=11)]
        max_depth.append(None)

        self.reg = RandomForestRegressor()
        self.param_grid = {'n_estimators': [int(x) for x in np.linspace(start=200, stop=2000, num=10)],
                           'max_depth': max_depth,
                           'min_samples_split': [2, 5, 10],
                           'min_samples_leaf': [1, 2, 4],
                           'max_features': ['auto', 'sqrt'],
                           'bootstrap': [True, False]
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

    def save(self, city_name, sensor, pollutant):
        with open(MODELS_PATH + '/' + city_name + '/' + sensor['id'] + '/' + pollutant + '/' + type(self).__name__
                  + '/random_forest_regression_model.pkl', 'wb') as out_file:
            pickle.dump(self.reg, out_file, pickle.HIGHEST_PROTOCOL)

    def load(self, city_name, sensor, pollutant):
        with open(MODELS_PATH + '/' + city_name + '/' + sensor['id'] + '/' + pollutant + '/' + type(self).__name__
                  + '/random_forest_regression_model.pkl', 'rb') as in_file:
            self.reg = pickle.load(in_file)
