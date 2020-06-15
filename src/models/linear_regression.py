from pickle import dump as pickle_dump, load as pickle_load, HIGHEST_PROTOCOL

from sklearn.linear_model import LinearRegression

from definitions import MODELS_PATH


class LinearRegressionModel:
    def __init__(self):
        self.reg = LinearRegression()
        self.param_grid = {
            'fit_intercept': [True, False],
            'normalize': [True, False],
            'copy_X': [True, False]
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
        with open(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + type(self).__name__
                  + '/linear_regression_model.pkl', 'wb') as out_file:
            pickle_dump(self.reg, out_file, HIGHEST_PROTOCOL)

    def load(self, city_name, sensor_id, pollutant):
        with open(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + type(self).__name__
                  + '/linear_regression_model.pkl', 'rb') as in_file:
            self.reg = pickle_load(in_file)
