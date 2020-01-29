import pickle

import numpy as np
from sklearn.svm import SVR

from definitions import MODELS_PATH


class SupportVectorRegressionModel:
    def __init__(self):
        max_depth = [int(x) for x in np.linspace(10, 110, num=11)]
        max_depth.append(None)

        self.reg = SVR()
        self.param_grid = {'kernel': ['rbf'],
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

    def save(self, station, pollutant):
        with open(MODELS_PATH + '/' + station + '/' + pollutant + '/' + type(
                self).__name__ + '/support_vector_regression_model.pkl', 'wb') as out_file:
            pickle.dump(self.reg, out_file, pickle.HIGHEST_PROTOCOL)

    def load(self, station, pollutant):
        with open(MODELS_PATH + '/' + station + '/' + pollutant + '/' + type(
                self).__name__ + '/support_vector_regression_model.pkl', 'rb') as in_file:
            self.reg = pickle.load(in_file)
