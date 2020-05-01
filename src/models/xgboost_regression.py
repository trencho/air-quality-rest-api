import os
import pickle

from xgboost.sklearn import XGBRegressor

from definitions import MODELS_PATH


class XGBoostRegressionModel:
    def __init__(self):
        self.reg = XGBRegressor()
        self.param_grid = {
            'n_jobs': [os.cpu_count() // 2],
            'learning_rate': [.03, 0.05, .07],
            'max_depth': [5, 6, 7],
            'min_child_weight': [4],
            'verbosity ': [0],
            'subsample': [0.7],
            'colsample_bytree': [0.7],
            'n_estimators': [500]
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
        with open(MODELS_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/' + type(self).__name__
                  + '/xgboost_regression_model.pkl', 'wb') as out_file:
            pickle.dump(self.reg, out_file, pickle.HIGHEST_PROTOCOL)

    def load(self, city_name, sensor, pollutant):
        with open(MODELS_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/' + type(self).__name__
                  + '/xgboost_regression_model.pkl', 'rb') as in_file:
            self.reg = pickle.load(in_file)
