import os
import pickle

from tpot import TPOTRegressor

from definitions import MODELS_PATH


class TPOTRegressionModel:
    def __init__(self):
        self.reg = TPOTRegressor(verbosity=3,
                                 random_state=55,
                                 periodic_checkpoint_folder="intermediate_results",
                                 n_jobs=os.cpu_count() / 2,
                                 warm_start=True,
                                 generations=20,
                                 population_size=80,
                                 early_stop=8)
        self.param_grid = {}

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
                  + '/tpot_regression_model.pkl', 'wb') as out_file:
            pickle.dump(self.reg, out_file, pickle.HIGHEST_PROTOCOL)

    def load(self, city_name, sensor, pollutant):
        with open(MODELS_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/' + type(self).__name__
                  + '/tpot_regression_model.pkl', 'rb') as in_file:
            self.reg = pickle.load(in_file)
