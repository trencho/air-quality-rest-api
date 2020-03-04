import pickle

from sklearn.neural_network import MLPRegressor

from definitions import MODELS_PATH


class MLPRegressionModel:
    def __init__(self):
        self.reg = MLPRegressor()
        self.param_grid = {
            'hidden_layer_sizes': [i for i in range(1, 15)],
            'max_iter': [1000]
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
                  + '/mlp_regression_model.pkl', 'wb') as out_file:
            pickle.dump(self.reg, out_file, pickle.HIGHEST_PROTOCOL)

    def load(self, city_name, sensor, pollutant):
        with open(MODELS_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/' + type(self).__name__
                  + '/mlp_regression_model.pkl', 'rb') as in_file:
            self.reg = pickle.load(in_file)
