import pickle

from sklearn.linear_model import LogisticRegression

from definitions import MODELS_PATH


class LogisticRegressionModel:
    def __init__(self):
        self.reg = LogisticRegression()
        self.param_grid = {'penalty': ['l1', 'l2'],
                           'C': [0.0001, 0.001, 0.01, 0.1, 1, 10, 100, 1000],
                           'class_weight': [{1: 0.5, 0: 0.5}, {1: 0.4, 0: 0.6}, {1: 0.6, 0: 0.4}, {1: 0.7, 0: 0.3}],
                           'solver': ['liblinear', 'saga']
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
                  + '/logistic_regression_model.pkl', 'wb') as out_file:
            pickle.dump(self.reg, out_file, pickle.HIGHEST_PROTOCOL)

    def load(self, city_name, sensor, pollutant):
        with open(MODELS_PATH + '/' + city_name + '/' + sensor['id'] + '/' + pollutant + '/' + type(self).__name__
                  + '/logistic_regression_model.pkl', 'rb') as in_file:
            self.reg = pickle.load(in_file)
