import math
import os
import pickle

import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn.model_selection import RandomizedSearchCV

from definitions import DATA_RAW_PATH, RESULTS_PREDICTIONS_PATH, RESULTS_ERRORS_PATH, MODELS_PATH
from definitions import stations, pollutants
from src.models import make_model
from src.processing import generate_features, backward_elimination
from src.visualization import draw_errors, draw_predictions

timestamp_2018 = 1514764800

regression_models = [
    'DecisionTreeRegressionModel',
    'DummyRegressionModel',
    'LightGBMRegressionModel',
    'LinearRegressionModel',
    # 'LogisticRegressionModel',
    'RandomForestRegressionModel',
    'SupportVectorRegressionModel',
    'TPOTRegressionModel',
    'XGBoostRegressionModel'
]


def create_model_paths(station, pollutant, model_name):
    if not os.path.exists(MODELS_PATH + '/' + station + '/' + pollutant + '/' + model_name + '/'):
        os.makedirs(MODELS_PATH + '/' + station + '/' + pollutant + '/' + model_name + '/')

    if not os.path.exists(RESULTS_ERRORS_PATH + '/data/' + station + '/' + pollutant + '/' + model_name + '/'):
        os.makedirs(RESULTS_ERRORS_PATH + '/data/' + station + '/' + pollutant + '/' + model_name + '/')

    if not os.path.exists(RESULTS_PREDICTIONS_PATH + '/data/' + station + '/' + pollutant + '/' + model_name + '/'):
        os.makedirs(RESULTS_PREDICTIONS_PATH + '/data/' + station + '/' + pollutant + '/' + model_name + '/')


def check_model_lock(station, pollutant, model_name):
    if os.path.exists(MODELS_PATH + '/' + station + '/' + pollutant + '/' + model_name + '/.lock'):
        return True

    return False


def create_model_lock(station, pollutant, model_name):
    with open(MODELS_PATH + '/' + station + '/' + pollutant + '/' + model_name + '/.lock', 'w'):
        pass


def remove_model_lock(station, pollutant, model_name):
    os.remove(MODELS_PATH + '/' + station + '/' + pollutant + '/' + model_name + '/.lock')


def split_dataset(dataset, pollutant):
    train_dataset = dataset[dataset['time'] < timestamp_2018]
    test_dataset = dataset[dataset['time'] >= timestamp_2018]

    X_train = train_dataset.drop(columns=pollutant, errors='ignore')
    # X_train = min_max_scaling(X_train)
    y_train = train_dataset[pollutant]

    # X_train, y_train = previous_value_overwrite(X_train, y_train)

    selected_features = backward_elimination(X_train, y_train)
    X_train = X_train[selected_features]

    X_test = test_dataset.drop(columns=pollutant, errors='ignore')
    # X_test = min_max_scaling(X_test)

    y_test = test_dataset[pollutant]

    # X_test, y_test = previous_value_overwrite(X_test, y_test)

    X_test = X_test[selected_features]

    return X_train, X_test, y_train, y_test


def generate_regression_model(dataset, station, pollutant):
    dataframe = generate_features(dataset, pollutant)

    X_train, X_test, y_train, y_test = split_dataset(dataframe, pollutant)

    selected_features = X_train.columns
    save_selected_features(station, pollutant, selected_features)
    best_model_error = math.inf
    best_model = None
    for model_name in regression_models:
        create_model_paths(station, pollutant, model_name)
        is_model_locked = check_model_lock(station, pollutant, model_name)
        if is_model_locked:
            continue
        create_model_lock(station, pollutant, model_name)

        model = make_model(model_name)
        params = hyper_parameter_tuning(model, X_train, y_train, station, pollutant)
        model.set_params(**params)
        model.train(X_train, y_train)

        model.save(station, pollutant)

        y_pred = model.predict(X_test)

        df = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
        df.to_csv(
            RESULTS_PREDICTIONS_PATH + '/data/' + station + '/' + pollutant + '/' + model_name + '/prediction.csv',
            index=False)

        model_error = save_errors(model_name, station, pollutant, y_test, y_pred)
        if model_error < best_model_error:
            best_model = model.reg

        remove_model_lock(station, pollutant, model_name)

    with open(MODELS_PATH + '/' + station + '/' + pollutant + '/best_regression_model.pkl', 'wb') as out_file:
        pickle.dump(best_model, out_file, pickle.HIGHEST_PROTOCOL)

    draw_errors()
    draw_predictions()


def previous_value_overwrite(X, y):
    time_column = X['time']
    time_column.drop(time_column.size - 1, inplace=True)

    X = X.shift(periods=-1, axis=0)
    X.reset_index(drop=True, inplace=True)
    X['time'] = time_column
    X.drop(len(X) - 1, inplace=True)

    y = y.reset_index(drop=True)
    y = y.drop(y.size - 1)

    return X, y


def hyper_parameter_tuning(model, X_train, y_train, station, pollutant):
    # dt_cv = GridSearchCV(model.reg, model.param_grid, n_jobs=-1, cv=5)
    dt_cv = RandomizedSearchCV(model.reg, model.param_grid, cv=5)
    dt_cv.fit(X_train, y_train)

    with open(RESULTS_PREDICTIONS_PATH + '/data/' + station + '/' + pollutant + '/' + type(
            model).__name__ + '/HyperparameterOptimization.txt', 'w') as out_file:
        out_file.write('Best Hyperparameters::\n{}'.format(dt_cv.best_params_))

    return dt_cv.best_params_


def save_selected_features(station, pollutant, selected_features):
    with open(MODELS_PATH + '/' + station + '/' + pollutant + '/selected_features.txt', 'w') as out_file:
        out_file.write(str(selected_features))


def save_errors(model_name, station, pollutant, y_test, y_pred):
    df = pd.DataFrame({'Mean Absolute Error': [metrics.mean_absolute_error(y_test, y_pred)],
                       'Mean Squared Error': [metrics.mean_squared_error(y_test, y_pred)],
                       'Root Mean Squared Error': [np.sqrt(metrics.mean_squared_error(y_test, y_pred))]},
                      columns=['Mean Absolute Error', 'Mean Squared Error', 'Root Mean Squared Error'])
    df.to_csv(RESULTS_ERRORS_PATH + '/data/' + station + '/' + pollutant + '/' + model_name + '/error.csv', index=False)

    return metrics.mean_absolute_error(y_test, y_pred)


def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def train(station=None, pollutant=None):
    if station is not None and pollutant is None:
        dataset = pd.read_csv(DATA_RAW_PATH + '/combined/combined_report_' + station + '.csv')
        for pollutant in pollutants:
            generate_regression_model(dataset, station, pollutant)
    elif station is None and pollutant is not None:
        for station in stations:
            dataset = pd.read_csv(DATA_RAW_PATH + '/combined/combined_report_' + station + '.csv')
            generate_regression_model(dataset, station, pollutant)
    else:
        for station in stations:
            dataset = pd.read_csv(DATA_RAW_PATH + '/combined/combined_report_' + station + '.csv')
            for pollutant in pollutants:
                generate_regression_model(dataset, station, pollutant)
