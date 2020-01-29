import pickle

from sklearn.dummy import DummyRegressor

from definitions import MODELS_PATH


class DummyRegressionModel:
    def __init__(self):
        self.reg = DummyRegressor()
        self.param_grid = {'strategy': ['mean', 'median', 'quantile'],
                           'quantile': [0.0, 0.5, 1.0]
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
                self).__name__ + '/dummy_regression_model.pkl', 'wb') as out_file:
            pickle.dump(self.reg, out_file, pickle.HIGHEST_PROTOCOL)

    def load(self, station, pollutant):
        with open(MODELS_PATH + '/' + station + '/' + pollutant + '/' + type(
                self).__name__ + '/dummy_regression_model.pkl', 'rb') as in_file:
            self.reg = pickle.load(in_file)
