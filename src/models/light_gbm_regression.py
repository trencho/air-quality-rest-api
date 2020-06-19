from os import path
from pickle import dump as pickle_dump, load as pickle_load, HIGHEST_PROTOCOL

from lightgbm import LGBMRegressor

from definitions import MODELS_PATH


class LightGBMRegressionModel:
    def __init__(self):
        self.reg = LGBMRegressor()
        self.param_grid = {
            'num_leaves': (6, 50),
            'min_child_samples': (100, 500),
            'min_child_weight': [1e-5, 1e-3, 1e-2, 1e-1, 1, 1e1, 1e2, 1e3, 1e4],
            'subsample': (0.2, 0.8),
            'colsample_bytree': (0.4, 0.6),
            'reg_alpha': [0, 1e-1, 1, 2, 5, 7, 10, 50, 100],
            'reg_lambda': [0, 1e-1, 1, 5, 10, 20, 50, 100]
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
                            'light_gbm_regression_model.pkl', 'wb')) as out_file:
            pickle_dump(self.reg, out_file, HIGHEST_PROTOCOL)

    def load(self, city_name, sensor_id, pollutant):
        with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, type(self).__name__,
                            'light_gbm_regression_model.pkl', 'rb')) as in_file:
            self.reg = pickle_load(in_file)
