from datetime import datetime
from math import inf
from os import environ, makedirs, path, remove
from pickle import dump, HIGHEST_PROTOCOL
from threading import Thread
from warnings import catch_warnings, simplefilter

from pandas import DataFrame, read_csv, Series, to_datetime
from sklearn.model_selection import RandomizedSearchCV

from api.config.logger import log
from definitions import app_dev, app_env, DATA_PROCESSED_PATH, MODELS_PATH, pollutants, regression_models, \
    RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH
from models import make_model
from models.base_regression_model import BaseRegressionModel
from processing import backward_elimination, current_hour, encode_categorical_data, generate_features, value_scaling
from visualization import draw_errors, draw_predictions
from .process_results import save_errors, save_results

lock_file = '.lock'


def previous_value_overwrite(dataframe: DataFrame) -> DataFrame:
    dataframe = dataframe.shift(periods=-1, axis=0)
    dataframe.drop(dataframe.tail(1).index, inplace=True)

    return dataframe


def split_dataframe(dataframe: DataFrame, target: str, selected_features: list = None) -> tuple:
    x = dataframe.drop(columns=pollutants, errors='ignore')
    x = value_scaling(x)
    y = dataframe[target]

    x = previous_value_overwrite(x)
    y = y.drop(y.tail(1).index)

    selected_features = backward_elimination(x, y) if selected_features is None else selected_features
    x = x[selected_features]

    return x, y


def save_selected_features(city_name: str, sensor_id: str, pollutant: str, selected_features: list) -> None:
    makedirs(path.join(MODELS_PATH, city_name, sensor_id, pollutant), exist_ok=True)
    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, 'selected_features.pkl'), 'wb') as out_file:
        dump(selected_features, out_file, HIGHEST_PROTOCOL)


def read_model(city_name: str, sensor_id: str, pollutant: str, algorithm: str, error_type: str) -> tuple:
    dataframe_errors = read_csv(
        path.join(RESULTS_ERRORS_PATH, 'data', city_name, sensor_id, pollutant, algorithm, 'error.csv'))
    model = make_model(algorithm)
    model.load(path.join(MODELS_PATH, city_name, sensor_id, pollutant))
    return model, dataframe_errors.iloc[0][error_type]


def create_models_path(city_name: str, sensor_id: str, pollutant: str, model_name: str) -> None:
    makedirs(path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name), exist_ok=True)


def create_results_path(results_path: str, city_name: str, sensor_id: str, pollutant: str, model_name: str) -> None:
    makedirs(path.join(results_path, 'data', city_name, sensor_id, pollutant, model_name), exist_ok=True)


def create_paths(city_name: str, sensor_id: str, pollutant: str, model_name: str) -> None:
    create_models_path(city_name, sensor_id, pollutant, model_name)
    create_results_path(RESULTS_ERRORS_PATH, city_name, sensor_id, pollutant, model_name)
    create_results_path(RESULTS_PREDICTIONS_PATH, city_name, sensor_id, pollutant, model_name)


def check_pollutant_lock(city_name: str, sensor_id: str, pollutant: str) -> bool:
    return path.exists(path.join(MODELS_PATH, city_name, sensor_id, pollutant, lock_file))


def create_pollutant_lock(city_name: str, sensor_id: str, pollutant: str) -> None:
    makedirs(path.join(MODELS_PATH, city_name, sensor_id, pollutant), exist_ok=True)
    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, lock_file), 'w'):
        pass


def hyper_parameter_tuning(model: BaseRegressionModel, x_train: DataFrame, y_train: Series, city_name: str,
                           sensor_id: str, pollutant: str):
    model_cv = RandomizedSearchCV(model.reg, model.param_grid, cv=5)
    model_cv.fit(x_train, y_train)

    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, type(model).__name__,
                        'HyperparameterOptimization.pkl'), 'wb') as out_file:
        dump(model_cv.best_params_, out_file, HIGHEST_PROTOCOL)

    return model_cv.best_params_


def remove_pollutant_lock(city_name: str, sensor_id: str, pollutant: str) -> None:
    try:
        remove(path.join(MODELS_PATH, city_name, sensor_id, pollutant, lock_file))
    except OSError:
        pass


def check_best_regression_model(city_name: str, sensor_id: str, pollutant: str) -> bool:
    try:
        last_modified = int(
            path.getmtime(path.join(MODELS_PATH, city_name, sensor_id, pollutant, 'best_regression_model.pkl')))
        month_in_seconds = 2629800
        if last_modified < int(datetime.timestamp(current_hour())) - month_in_seconds:
            return False

        return True
    except OSError:
        return False


def save_best_regression_model(city_name: str, sensor_id: str, pollutant: str, best_model: BaseRegressionModel) -> None:
    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, 'best_regression_model.pkl'), 'wb') as out_file:
        dump(best_model, out_file, HIGHEST_PROTOCOL)


def generate_regression_model(dataframe: DataFrame, city_name: str, sensor_id: str, pollutant: str) -> None:
    dataframe = dataframe.join(generate_features(dataframe[pollutant]), how='inner')
    encode_categorical_data(dataframe)
    validation_split = len(dataframe.index) * 3 // 4

    train_dataframe = dataframe.iloc[:validation_split]
    x_train, y_train = split_dataframe(train_dataframe, pollutant)
    selected_features = x_train.columns.values.tolist()

    test_dataframe = dataframe.iloc[validation_split:]
    x_test, y_test = split_dataframe(test_dataframe, pollutant, selected_features)

    save_selected_features(city_name, sensor_id, pollutant, selected_features)

    best_model_error = inf
    best_model = None
    for model_name in regression_models:
        if (env_var := environ.get(app_env, app_dev)) == app_dev and path.exists(
                path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name, f'{model_name}.pkl')):
            model, model_error = read_model(city_name, sensor_id, pollutant, model_name, 'Mean Absolute Error')
            if model_error < best_model_error:
                best_model = model
                best_model_error = model_error
            continue

        create_paths(city_name, sensor_id, pollutant, model_name)

        model = make_model(model_name)
        params = hyper_parameter_tuning(model, x_train, y_train, city_name, sensor_id, pollutant)
        model.set_params(**params)
        model.train(x_train, y_train)

        if env_var == app_dev:
            model.save(path.join(MODELS_PATH, city_name, sensor_id, pollutant))

        with catch_warnings():
            simplefilter('ignore')
            y_predicted = model.predict(x_test)

        results = DataFrame({'Actual': y_test, 'Predicted': y_predicted}, x_test.index)
        save_results(city_name, sensor_id, pollutant, model_name, results)

        if (model_error := save_errors(city_name, sensor_id, pollutant, model_name, y_test,
                                       y_predicted)) < best_model_error:
            best_model = model
            best_model_error = model_error

    if best_model is not None:
        x_train, y_train = split_dataframe(dataframe, pollutant, selected_features)
        best_model.train(x_train, y_train)
        save_best_regression_model(city_name, sensor_id, pollutant, best_model.reg)


def train_regression_model(city: dict, sensor: dict, pollutant: str) -> None:
    if check_best_regression_model(city['cityName'], sensor['sensorId'], pollutant) or check_pollutant_lock(
            city['cityName'], sensor['sensorId'], pollutant):
        return
    try:
        dataframe = read_csv(path.join(DATA_PROCESSED_PATH, city['cityName'], sensor['sensorId'], 'summary.csv'),
                             index_col='time', engine='python')
        dataframe.index = to_datetime(dataframe.index, unit='s')
        dataframe = dataframe.loc[dataframe.index <= current_hour()]
        if pollutant in dataframe.columns:
            create_pollutant_lock(city['cityName'], sensor['sensorId'], pollutant)
            generate_regression_model(dataframe, city['cityName'], sensor['sensorId'], pollutant)
            draw_errors(city, sensor, pollutant)
            draw_predictions(city, sensor, pollutant)
    except Exception:
        log.error(f'Error occurred while training regression model for {city["cityName"]} - {sensor["sensorId"]} - '
                  f'{pollutant}', exc_info=1)
    finally:
        remove_pollutant_lock(city['cityName'], sensor['sensorId'], pollutant)


def train_city_sensors(city: dict, sensor: dict, pollutant: str) -> None:
    Thread(target=train_regression_model, args=(city, sensor, pollutant), daemon=True).start()
