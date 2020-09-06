from math import inf
from os import makedirs, path, remove as os_remove
from pickle import dump as pickle_dump, HIGHEST_PROTOCOL

from pandas import DataFrame, read_csv, to_datetime
from sklearn.model_selection import RandomizedSearchCV

from definitions import DATA_EXTERNAL_PATH, MODELS_PATH, RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH, pollutants, \
    regression_models
from models import make_model
from processing import generate_features, previous_value_overwrite, value_scaling
from visualization import draw_errors, draw_predictions
from .process_results import save_errors, save_results


def split_dataframe(dataframe, pollutant, selected_features=None):
    x = dataframe.drop(columns=pollutants, errors='ignore')
    x = value_scaling(x)
    y = dataframe[pollutant]

    x = previous_value_overwrite(x)
    y.drop(y.tail(1).index, inplace=True)

    # selected_features = backward_elimination(x, y) if selected_features is None else selected_features
    # x = x[selected_features]

    return x, y


def save_selected_features(city_name, sensor_id, pollutant, selected_features):
    if not path.exists(path.join(MODELS_PATH, city_name, sensor_id, pollutant)):
        makedirs(path.join(MODELS_PATH, city_name, sensor_id, pollutant))
    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, 'selected_features.pkl'), 'wb') as out_file:
        pickle_dump(selected_features, out_file, HIGHEST_PROTOCOL)


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


def hyper_parameter_tuning(model, x_train, y_train, city_name, sensor_id, pollutant):
    # dt_cv = GridSearchCV(model.reg, model.param_grid, cv=5)
    dt_cv = RandomizedSearchCV(model.reg, model.param_grid, cv=5)
    dt_cv.fit(x_train, y_train)

    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, type(model).__name__,
                        'HyperparameterOptimization.pkl'), 'wb') as out_file:
        pickle_dump(dt_cv.best_params_, out_file, HIGHEST_PROTOCOL)

    return dt_cv.best_params_


def remove_model_lock(city_name, sensor_id, pollutant, model_name):
    os_remove(path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name, '.lock'))


def save_best_regression_model(city_name, sensor_id, pollutant, best_model):
    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, 'best_regression_model.pkl'), 'wb') as out_file:
        pickle_dump(best_model, out_file, HIGHEST_PROTOCOL)


def generate_regression_model(dataframe, city_name, sensor_id, pollutant):
    dataframe = dataframe.join(generate_features(dataframe[pollutant]), how='outer').dropna()

    validation_split = len(dataframe) * 3 // 4

    train_dataframe = dataframe.iloc[:validation_split]
    x_train, y_train = split_dataframe(train_dataframe, pollutant)
    selected_features = list(x_train.columns)

    test_dataframe = dataframe.iloc[validation_split:]
    x_test, y_test = split_dataframe(test_dataframe, pollutant, selected_features)

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
        params = hyper_parameter_tuning(model, x_train, y_train, city_name, sensor_id, pollutant)
        model.set_params(**params)
        model.train(x_train, y_train)
        model.save(city_name, sensor_id, pollutant)

        y_predicted = model.predict(x_test)

        results = DataFrame({'Actual': y_test, 'Predicted': y_predicted}, x_test.index)
        save_results(city_name, sensor_id, pollutant, model_name, results)

        model_error = save_errors(city_name, sensor_id, pollutant, model_name, y_test, y_predicted)
        if model_error < best_model_error:
            best_model = model
            best_model_error = model_error

        remove_model_lock(city_name, sensor_id, pollutant, model_name)

    if best_model is not None:
        x_train, y_train = split_dataframe(dataframe, pollutant, selected_features)
        best_model.train(x_train, y_train)
        save_best_regression_model(city_name, sensor_id, pollutant, best_model.reg)


def train_regression_model(city, sensor, pollutant):
    try:
        dataframe = read_csv(path.join(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId'], 'summary.csv'))
        dataframe.set_index(to_datetime(dataframe['time'], unit='s'), inplace=True)
        dataframe.drop(dataframe.columns.difference([pollutant]), axis=1, inplace=True)
        if pollutant in dataframe.columns:
            generate_regression_model(dataframe, city['cityName'], sensor['sensorId'], pollutant)
            draw_errors(city, sensor, pollutant)
            draw_predictions(city, sensor, pollutant)
    except FileNotFoundError:
        pass
