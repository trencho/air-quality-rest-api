import math
import os
import pickle

import pandas as pd
from sklearn.model_selection import GridSearchCV

from definitions import DATA_EXTERNAL_PATH, MODELS_PATH, RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH
from definitions import pollutants
from modeling import save_errors
from src.models import make_model
from src.processing import backward_elimination, generate_features
from src.visualization import draw_errors, draw_predictions

timestamp_2018 = 1514764800

regression_models = [
    'DecisionTreeRegressionModel',
    'DummyRegressionModel',
    'LightGBMRegressionModel',
    'LinearRegressionModel',
    'RandomForestRegressionModel',
    'SupportVectorRegressionModel',
    'TPOTRegressionModel',
    'XGBoostRegressionModel'
]


def create_model_paths(city_name, sensor, pollutant, model_name):
    if not os.path.exists(
            MODELS_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/' + model_name + '/'):
        os.makedirs(MODELS_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/' + model_name + '/')

    if not os.path.exists(RESULTS_ERRORS_PATH + '/data/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/'
                          + model_name + '/'):
        os.makedirs(RESULTS_ERRORS_PATH + '/data/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/'
                    + model_name + '/')

    if not os.path.exists(RESULTS_PREDICTIONS_PATH + '/data/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant
                          + '/' + model_name + '/'):
        os.makedirs(RESULTS_PREDICTIONS_PATH + '/data/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/'
                    + model_name + '/')


def check_model_lock(city_name, sensor, pollutant, model_name):
    return os.path.exists(
        MODELS_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/' + model_name + '/.lock')


def create_model_lock(city_name, sensor, pollutant, model_name):
    with open(MODELS_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/' + model_name + '/.lock',
              'w'):
        pass


def remove_model_lock(city_name, sensor, pollutant, model_name):
    os.remove(MODELS_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/' + model_name + '/.lock')


def split_dataset(dataset, pollutant):
    train_dataset = dataset[dataset['time'] < timestamp_2018]
    test_dataset = dataset[dataset['time'] >= timestamp_2018]

    X_train = train_dataset.drop(columns=pollutant, errors='ignore')
    # X_train = min_max_scaling(X_train)
    y_train = train_dataset[pollutant]

    X_train, y_train = previous_value_overwrite(X_train, y_train)

    selected_features = backward_elimination(X_train, y_train)
    X_train = X_train[selected_features]

    X_test = test_dataset.drop(columns=pollutant, errors='ignore')
    # X_test = min_max_scaling(X_test)

    y_test = test_dataset[pollutant]

    X_test, y_test = previous_value_overwrite(X_test, y_test)

    X_test = X_test[selected_features]

    return X_train, X_test, y_train, y_test


def generate_regression_model(dataset, city_name, sensor, pollutant):
    dataframe = generate_features(dataset, pollutant)

    X_train, X_test, y_train, y_test = split_dataset(dataframe, pollutant)

    selected_features = X_train.columns
    save_selected_features(city_name, sensor, pollutant, selected_features)
    best_model_error = math.inf
    best_model = None
    for model_name in regression_models:
        create_model_paths(city_name, sensor, pollutant, model_name)
        is_model_locked = check_model_lock(city_name, sensor, pollutant, model_name)
        if is_model_locked:
            continue
        create_model_lock(city_name, sensor, pollutant, model_name)

        model = make_model(model_name)
        params = hyper_parameter_tuning(model, X_train, y_train, city_name, sensor, pollutant)
        model.set_params(**params)
        model.train(X_train, y_train)

        model.save(city_name, sensor, pollutant)

        y_pred = model.predict(X_test)

        df = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
        df.to_csv(RESULTS_PREDICTIONS_PATH + '/data/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/'
                  + model_name + '/prediction.csv', index=False)

        model_error = save_errors(model_name, city_name, sensor, pollutant, y_test, y_pred)
        if model_error < best_model_error:
            best_model = model.reg

        remove_model_lock(city_name, sensor, pollutant, model_name)

    with open(MODELS_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/best_regression_model.pkl',
              'wb') as out_file:
        pickle.dump(best_model, out_file, pickle.HIGHEST_PROTOCOL)

    draw_errors(city_name, sensor, pollutant)
    draw_predictions(city_name, sensor, pollutant)


def previous_value_overwrite(X, y):
    X = X.shift(periods=-1, axis=0)
    X.reset_index(drop=True, inplace=True)
    X.drop(len(X) - 1, inplace=True)

    y = y.reset_index(drop=True)
    y.drop(len(y) - 1, inplace=True)

    return X, y


def hyper_parameter_tuning(model, X_train, y_train, city_name, sensor, pollutant):
    dt_cv = GridSearchCV(model.reg, model.param_grid, n_jobs=os.cpu_count() / 2, cv=5)
    dt_cv.fit(X_train, y_train)

    with open(RESULTS_PREDICTIONS_PATH + '/data/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/'
              + type(model).__name__ + '/HyperparameterOptimization.txt', 'w') as out_file:
        out_file.write('Best Hyperparameters::\n{}'.format(dt_cv.best_params_))

    return dt_cv.best_params_


def save_selected_features(city_name, sensor, pollutant, selected_features):
    with open(MODELS_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/selected_features.txt',
              'w') as out_file:
        out_file.write(str(selected_features))


def train(city_name, sensor, pollutant=None):
    dataset = pd.read_csv(
        DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/weather_pollution_report.csv')
    if pollutant is not None:
        generate_regression_model(dataset, city_name, sensor, pollutant)
    else:
        for pollutant in pollutants:
            if pollutant not in dataset.columns:
                return
            generate_regression_model(dataset, city_name, sensor, pollutant)
