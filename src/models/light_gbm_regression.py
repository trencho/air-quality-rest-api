import pickle

import lightgbm as lgb
from scipy.stats import randint as sp_randint
from scipy.stats import uniform as sp_uniform

from definitions import MODELS_PATH


class LightGBMRegressionModel:
    def __init__(self):
        self.reg = lgb.LGBMRegressor()
        self.param_grid = {'num_leaves': sp_randint(6, 50),
                           'min_child_samples': sp_randint(100, 500),
                           'min_child_weight': [1e-5, 1e-3, 1e-2, 1e-1, 1, 1e1, 1e2, 1e3, 1e4],
                           'subsample': sp_uniform(loc=0.2, scale=0.8),
                           'colsample_bytree': sp_uniform(loc=0.4, scale=0.6),
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

    def save(self, city_name, sensor, pollutant):
        with open(MODELS_PATH + '/' + city_name + '/' + sensor['id'] + '/' + pollutant + '/' + type(self).__name__
                  + '/light_gbm_regression_model.pkl', 'wb') as out_file:
            pickle.dump(self.reg, out_file, pickle.HIGHEST_PROTOCOL)

    def load(self, city_name, sensor, pollutant):
        with open(MODELS_PATH + '/' + city_name + '/' + sensor['id'] + '/' + pollutant + '/' + type(self).__name__
                  + '/light_gbm_regression_model.pkl', 'rb') as in_file:
            self.reg = pickle.load(in_file)
