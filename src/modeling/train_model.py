from math import inf
from os import makedirs, path, remove as os_remove
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


def drop_columns(dataframe, columns):
    return dataframe.drop(columns=columns, errors='ignore')


def split_dataframe(dataframe, pollutant, selected_features=None):
    X = drop_columns(dataframe, pollutants)
    X = value_scaling(X)
    y = dataframe[pollutant]

    X, y = previous_value_overwrite(X, y)
    selected_features = backward_elimination(X, y) if selected_features is None else selected_features
    X = X[selected_features]

    return X, y


def save_selected_features(city_name, sensor_id, pollutant, selected_features):
    if not path.exists(path.join(MODELS_PATH, city_name, sensor_id, pollutant)):
        makedirs(path.join(MODELS_PATH, city_name, sensor_id, pollutant))
    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, 'selected_features.txt'), 'wb') as out_file:
        pickle_dump(selected_features, out_file)


def create_models_path(city_name, sensor_id, pollutant, model_name):
    if not path.exists(path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name)):
        makedirs(path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name))


def create_results_path(results_path, city_name, sensor_id, pollutant, model_name):
    if not path.exists(path.join(results_path, 'data', city_name, sensor_id, pollutant, model_name)):
        makedirs(path.join(results_path, 'data', city_name, sensor_id, pollutant, model_name))


def create_paths(city_name, sensor_id, pollutant, model_name):
    create_models_path(city_name, sensor_id, pollutant, model_name)
    create_results_path(RESULTS_ERRORS_PATH, city_name, sensor_id, pollutant, model_name)
    create_results_path(RESULTS_PREDICTIONS_PATH, city_name, sensor_id, pollutant, model_name)


def check_model_lock(city_name, sensor_id, pollutant, model_name):
    return path.exists(path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name, '.lock'))


def create_model_lock(city_name, sensor_id, pollutant, model_name):
    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name, '.lock'), 'w'):
        pass


def hyper_parameter_tuning(model, X_train, y_train, city_name, sensor_id, pollutant):
    # dt_cv = GridSearchCV(model.reg, model.param_grid, cv=5)
    dt_cv = RandomizedSearchCV(model.reg, model.param_grid, cv=5)
    dt_cv.fit(X_train, y_train)

    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, type(model).__name__,
                        'HyperparameterOptimization.txt'), 'wb') as out_file:
        pickle_dump(dt_cv.best_params_, out_file)

    return dt_cv.best_params_


def remove_model_lock(city_name, sensor_id, pollutant, model_name):
    os_remove(path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name, '.lock'))


def save_best_regression_model(city_name, sensor_id, pollutant, best_model):
    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, 'best_regression_model.pkl'), 'wb') as out_file:
        pickle_dump(best_model, out_file, HIGHEST_PROTOCOL)


def generate_regression_model(dataframe, city_name, sensor_id, pollutant):
    dataframe = generate_features(dataframe)

    validation_split = int(len(dataframe) * 3 / 4)

    train_dataframe = dataframe.iloc[:validation_split]
    X_train, y_train = split_dataframe(train_dataframe, pollutant)
    test_dataframe = dataframe.iloc[validation_split:]
    X_test, y_test = split_dataframe(test_dataframe, pollutant, X_train.columns)

    selected_features = list(X_train.columns)
    save_selected_features(city_name, sensor_id, pollutant, selected_features)

    best_model_error = inf
    best_model = None
    for model_name in regression_models:
        create_paths(city_name, sensor_id, pollutant, model_name)
        is_model_locked = check_model_lock(city_name, sensor_id, pollutant, model_name)
        if is_model_locked:
            continue
        create_model_lock(city_name, sensor_id, pollutant, model_name)

        model = make_model(model_name)
        params = hyper_parameter_tuning(model, X_train, y_train, city_name, sensor_id, pollutant)
        model.set_params(**params)
        model.train(X_train, y_train)

        model.save(city_name, sensor_id, pollutant)

        y_pred = model.predict(X_test)

        save_results(city_name, sensor_id, pollutant, model_name, y_test, y_pred)

        model_error = save_errors(city_name, sensor_id, pollutant, model_name, y_test, y_pred)
        if model_error < best_model_error:
            best_model = model
            best_model_error = model_error

        remove_model_lock(city_name, sensor_id, pollutant, model_name)

    if best_model is not None:
        X_train, y_train = split_dataframe(dataframe, pollutant)
        best_model.train(X_train, y_train)
        save_best_regression_model(city_name, sensor_id, pollutant, best_model.reg)


def train_regression_model(city, sensor, pollutant):
    dataframe = read_csv(path.join(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId'], 'summary_report.csv'))
    if pollutant in dataframe.columns:
        generate_regression_model(dataframe, city['cityName'], sensor['sensorId'], pollutant)
        draw_errors(city, sensor, pollutant)
        draw_predictions(city, sensor, pollutant)
