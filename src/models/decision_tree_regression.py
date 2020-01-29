import pickle

from sklearn.tree import DecisionTreeRegressor

from definitions import MODELS_PATH


class DecisionTreeRegressionModel:
    def __init__(self):
        self.reg = DecisionTreeRegressor()
        self.param_grid = {'criterion': ['mse', 'mae'],
                           'max_depth': [2, 6, 8],
                           'min_samples_split': [10, 20, 40],
                           'min_samples_leaf': [20, 40, 100],
                           'max_leaf_nodes': [5, 20, 100]
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
                self).__name__ + '/decision_tree_regression_model.pkl', 'wb') as out_file:
            pickle.dump(self.reg, out_file, pickle.HIGHEST_PROTOCOL)

    def load(self, station, pollutant):
        with open(MODELS_PATH + '/' + station + '/' + pollutant + '/' + type(
                self).__name__ + '/decision_tree_regression_model.pkl', 'rb') as in_file:
            self.reg = pickle.load(in_file)
