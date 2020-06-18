from math import inf
from os import cpu_count, makedirs, path, remove as os_remove
from pickle import dump as pickle_dump, HIGHEST_PROTOCOL

from pandas import read_csv
from sklearn.model_selection import RandomizedSearchCV

from definitions import DATA_EXTERNAL_PATH, MODELS_PATH, RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH, pollutants, \
    regression_models
from modeling import save_errors, save_results
from models import make_model
from processing import backward_elimination, generate_features, value_scaling
from visualization import draw_errors, draw_predictions


def previous_value_overwrite(X, y):
    X = X.shift(periods=-1, axis=0)
    X.reset_index(drop=True, inplace=True)
    X.drop(len(X) - 1, inplace=True)

    y = y.reset_index(drop=True)
    y.drop(len(y) - 1, inplace=True)

    return X, y


def split_dataset(dataset, pollutant):
    validation_split = len(dataset) * 3 // 4
    train_dataset = dataset.iloc[:validation_split]
    test_dataset = dataset.iloc[validation_split:]

    X_train = train_dataset.drop(columns=pollutants, errors='ignore')
    X_train = value_scaling(X_train)
    y_train = train_dataset[pollutant]

    X_train, y_train = previous_value_overwrite(X_train, y_train)

    selected_features = backward_elimination(X_train, y_train)
    X_train = X_train[selected_features]

    X_test = test_dataset.drop(columns=pollutants, errors='ignore')
    X_test = value_scaling(X_test)

    y_test = test_dataset[pollutant]

    X_test, y_test = previous_value_overwrite(X_test, y_test)

    X_test = X_test[selected_features]

    return X_train, X_test, y_train, y_test


def save_selected_features(city_name, sensor_id, pollutant, selected_features):
    if not path.exists(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/'):
        makedirs(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/')
    with open(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/selected_features.txt',
              'wb') as out_file:
        pickle_dump(selected_features, out_file)


def create_models_path(city_name, sensor_id, pollutant, model_name):
    if not path.exists(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + model_name + '/'):
        makedirs(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + model_name + '/')


def create_results_path(results_path, city_name, sensor_id, pollutant, model_name):
    if not path.exists(
            results_path + '/data/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + model_name + '/'):
        makedirs(results_path + '/data/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + model_name + '/')


def create_paths(city_name, sensor_id, pollutant, model_name):
    create_models_path(city_name, sensor_id, pollutant, model_name)
    create_results_path(RESULTS_ERRORS_PATH, city_name, sensor_id, pollutant, model_name)
    create_results_path(RESULTS_PREDICTIONS_PATH, city_name, sensor_id, pollutant, model_name)


def check_model_lock(city_name, sensor_id, pollutant, model_name):
    return path.exists(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + model_name + '/.lock')


def create_model_lock(city_name, sensor_id, pollutant, model_name):
    with open(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + model_name + '/.lock', 'w'):
        pass


def hyper_parameter_tuning(model, X_train, y_train, city_name, sensor_id, pollutant):
    # dt_cv = GridSearchCV(model.reg, model.param_grid, n_jobs=cpu_count() // 2, cv=5)
    dt_cv = RandomizedSearchCV(model.reg, model.param_grid, n_jobs=cpu_count() // 2, cv=5)
    dt_cv.fit(X_train, y_train)

    with open(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + type(model).__name__ +
              '/HyperparameterOptimization.txt', 'wb') as out_file:
        pickle_dump(dt_cv.best_params_, out_file)

    return dt_cv.best_params_


def remove_model_lock(city_name, sensor_id, pollutant, model_name):
    os_remove(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + model_name + '/.lock')


def save_best_regression_model(city_name, sensor_id, pollutant, best_model):
    with open(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/best_regression_model.pkl',
              'wb') as out_file:
        pickle_dump(best_model, out_file, HIGHEST_PROTOCOL)


def generate_regression_model(dataset, city, sensor, pollutant):
    dataframe = generate_features(dataset)

    X_train, X_test, y_train, y_test = split_dataset(dataframe, pollutant)

    selected_features = list(X_train.columns)
    save_selected_features(city['cityName'], sensor['sensorId'], pollutant, selected_features)

    best_model_error = inf
    best_model = None
    for model_name in regression_models:
        create_paths(city['cityName'], sensor['sensorId'], pollutant, model_name)
        is_model_locked = check_model_lock(city['cityName'], sensor['sensorId'], pollutant, model_name)
        if is_model_locked:
            continue
        create_model_lock(city['cityName'], sensor['sensorId'], pollutant, model_name)

        model = make_model(model_name)
        params = hyper_parameter_tuning(model, X_train, y_train, city['cityName'], sensor['sensorId'], pollutant)
        model.set_params(**params)
        model.train(X_train, y_train)

        model.save(city['cityName'], sensor['sensorId'], pollutant)

        y_pred = model.predict(X_test)

        save_results(city['cityName'], sensor['sensorId'], pollutant, model_name, y_test, y_pred)

        model_error = save_errors(city['cityName'], sensor['sensorId'], pollutant, model_name, y_test, y_pred)
        if model_error < best_model_error:
            best_model = model.reg
            best_model_error = model_error

        remove_model_lock(city['cityName'], sensor['sensorId'], pollutant, model_name)

    save_best_regression_model(city['cityName'], sensor['sensorId'], pollutant, best_model)

    draw_errors(city, sensor, pollutant)
    draw_predictions(city, sensor, pollutant)


def train(city, sensor, pollutant):
    dataset = read_csv(DATA_EXTERNAL_PATH + '/' + city['cityName'] + '/' + sensor['sensorId'] + '/summary_report.csv')
    if pollutant in dataset.columns:
        generate_regression_model(dataset, city, sensor, pollutant)
