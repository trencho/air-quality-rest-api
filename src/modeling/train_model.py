from datetime import datetime
from glob import glob
from math import inf
from os import environ, makedirs, path, remove
from pickle import dump, HIGHEST_PROTOCOL
from threading import Thread

from pandas import DataFrame, read_csv, Series
from sklearn.model_selection import RandomizedSearchCV

from api.config.logger import logger
from definitions import APP_DEV, APP_ENV, DATA_PROCESSED_PATH, MODELS_PATH, POLLUTANTS, REGRESSION_MODELS, \
    RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH
from models import make_model
from models.base_regression_model import BaseRegressionModel
from processing import backward_elimination, current_hour, encode_categorical_data, generate_features, \
    fetch_summary_dataframe, value_scaling
from visualization import draw_errors, draw_predictions
from .process_results import save_errors, save_results

LOCK_FILE = ".lock"


async def previous_value_overwrite(dataframe: DataFrame) -> DataFrame:
    dataframe = dataframe.shift(periods=-1, axis=0)
    return dataframe.drop(dataframe.tail(1).index)


async def split_dataframe(dataframe: DataFrame, target: str, selected_features: list = None) -> tuple:
    x = dataframe.drop(columns=POLLUTANTS, errors="ignore")
    x = await value_scaling(x)
    y = dataframe[target]

    x = await previous_value_overwrite(x)
    y = y.drop(y.tail(1).index)

    selected_features = await backward_elimination(x, y) if selected_features is None else selected_features
    x = x[selected_features]

    return x, y


async def save_selected_features(city_name: str, sensor_id: str, pollutant: str, selected_features: list) -> None:
    makedirs(path.join(MODELS_PATH, city_name, sensor_id, pollutant), exist_ok=True)
    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, "selected_features.pkl"), "wb") as out_file:
        dump(selected_features, out_file, HIGHEST_PROTOCOL)


async def read_model(city_name: str, sensor_id: str, pollutant: str, model_name: str, error_type: str) -> tuple:
    dataframe_errors = read_csv(
        path.join(RESULTS_ERRORS_PATH, "data", city_name, sensor_id, pollutant, model_name, "error.csv"))
    model = await make_model(model_name)
    await model.load(
        path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name))
    return model, dataframe_errors.iloc[0][error_type]


async def create_models_path(city_name: str, sensor_id: str, pollutant: str, model_name: str) -> None:
    makedirs(path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name), exist_ok=True)


async def create_results_path(results_path: str, city_name: str, sensor_id: str, pollutant: str,
                              model_name: str) -> None:
    makedirs(path.join(results_path, "data", city_name, sensor_id, pollutant, model_name), exist_ok=True)


async def create_paths(city_name: str, sensor_id: str, pollutant: str, model_name: str) -> None:
    await create_results_path(RESULTS_ERRORS_PATH, city_name, sensor_id, pollutant, model_name)
    await create_results_path(RESULTS_PREDICTIONS_PATH, city_name, sensor_id, pollutant, model_name)


async def check_pollutant_lock(city_name: str, sensor_id: str, pollutant: str) -> bool:
    return path.exists(path.join(MODELS_PATH, city_name, sensor_id, pollutant, LOCK_FILE))


async def create_pollutant_lock(city_name: str, sensor_id: str, pollutant: str) -> None:
    makedirs(path.join(MODELS_PATH, city_name, sensor_id, pollutant), exist_ok=True)
    with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, LOCK_FILE), "w"):
        pass


async def hyper_parameter_tuning(model: BaseRegressionModel, x_train: DataFrame, y_train: Series, city_name: str,
                                 sensor_id: str, pollutant: str) -> dict:
    model_cv = RandomizedSearchCV(model.reg, model.param_grid, cv=5)
    model_cv.fit(x_train, y_train)

    if environ.get(APP_ENV, APP_DEV) == APP_DEV:
        with open(path.join(MODELS_PATH, city_name, sensor_id, pollutant, type(model).__name__,
                            "HyperparameterOptimization.pkl"), "wb") as out_file:
            dump(model_cv.best_params_, out_file, HIGHEST_PROTOCOL)

    return model_cv.best_params_


async def remove_pollutant_lock(city_name: str, sensor_id: str, pollutant: str) -> None:
    try:
        remove(path.join(MODELS_PATH, city_name, sensor_id, pollutant, LOCK_FILE))
    except OSError:
        pass


async def check_best_regression_model(city_name: str, sensor_id: str, pollutant: str) -> bool:
    try:
        if not len(files := glob(path.join(MODELS_PATH, city_name, sensor_id, pollutant, "*.mdl"))):
            return False

        last_modified = int(path.getmtime(files[0]))
        month_in_seconds = 2629800
        if last_modified < int(datetime.timestamp(current_hour())) - month_in_seconds:
            remove(path.join(MODELS_PATH, city_name, sensor_id, pollutant, files[0]))
            return False

        return True
    except OSError:
        return False


async def generate_regression_model(dataframe: DataFrame, city_name: str, sensor_id: str, pollutant: str) -> None:
    dataframe = dataframe.join(await generate_features(dataframe[pollutant]), how="inner")
    dataframe = dataframe.dropna(axis="columns", how="all").dropna(axis="index", how="any")
    await encode_categorical_data(dataframe)
    validation_split = len(dataframe.index) * 3 // 4

    train_dataframe = dataframe.iloc[:validation_split]
    x_train, y_train = await split_dataframe(train_dataframe, pollutant)
    selected_features = x_train.columns.values.tolist()

    test_dataframe = dataframe.iloc[validation_split:]
    x_test, y_test = await split_dataframe(test_dataframe, pollutant, selected_features)

    best_model_error = inf
    best_model = None
    for model_name in REGRESSION_MODELS:
        if (env_var := environ.get(APP_ENV, APP_DEV)) == APP_DEV and path.exists(
                path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name, f"{model_name}.mdl")):
            await create_models_path(city_name, sensor_id, pollutant, model_name)
            model, model_error = await read_model(city_name, sensor_id, pollutant, model_name, "Mean Absolute Error")
            if model_error < best_model_error:
                best_model = model
                best_model_error = model_error
            continue

        await create_paths(city_name, sensor_id, pollutant, model_name)

        try:
            model = await setup_model(model_name, x_train, y_train, city_name, sensor_id, pollutant)
        except Exception:
            logger.error(
                f"Error occurred while training regression model for {city_name} - {sensor_id} - {pollutant} - "
                f"{model_name}", exc_info=True)
            continue

        if env_var == APP_DEV:
            await model.save(path.join(MODELS_PATH, city_name, sensor_id, pollutant, model_name))

        y_predicted = await model.predict(x_test)

        results = DataFrame({"Actual": y_test, "Predicted": y_predicted}, x_test.index)
        await save_results(city_name, sensor_id, pollutant, model_name, results)

        if (model_error := await save_errors(city_name, sensor_id, pollutant, model_name, y_test,
                                             y_predicted)) < best_model_error:
            best_model = model
            best_model_error = model_error

    if best_model is None:
        return

    await save_selected_features(city_name, sensor_id, pollutant, selected_features)
    x_train, y_train = await split_dataframe(dataframe, pollutant, selected_features)
    try:
        best_model = await setup_model(type(best_model).__name__, x_train, y_train, city_name, sensor_id, pollutant)
    except Exception:
        logger.error(f"Error occurred while training the best regression model for {city_name} - {sensor_id} - "
                     f"{pollutant} - {type(best_model).__name__}", exc_info=True)
    await best_model.save(path.join(MODELS_PATH, city_name, sensor_id, pollutant))


async def setup_model(model_name: str, x_train: DataFrame, y_train: Series, city_name: str, sensor_id: str,
                      pollutant: str) -> BaseRegressionModel:
    model = await make_model(model_name)
    params = await hyper_parameter_tuning(model, x_train, y_train, city_name, sensor_id, pollutant)
    await model.set_params(**params)
    await model.train(x_train, y_train)
    return model


async def train_regression_model(city: dict, sensor: dict, pollutant: str) -> None:
    if await check_best_regression_model(city["cityName"], sensor["sensorId"], pollutant) or await check_pollutant_lock(
            city["cityName"], sensor["sensorId"], pollutant):
        return
    try:
        dataframe = await fetch_summary_dataframe(path.join(DATA_PROCESSED_PATH, city["cityName"], sensor["sensorId"]),
                                                  index_col="time")
        dataframe = dataframe.loc[dataframe.index <= datetime.utcnow()]
        if pollutant in dataframe.columns:
            await create_pollutant_lock(city["cityName"], sensor["sensorId"], pollutant)
            await generate_regression_model(dataframe, city["cityName"], sensor["sensorId"], pollutant)
            await draw_errors(city, sensor, pollutant)
            await draw_predictions(city, sensor, pollutant)
    except Exception:
        logger.error(f"Error occurred while training regression model for {city['cityName']} - {sensor['sensorId']} - "
                     f"{pollutant}", exc_info=True)
    finally:
        await remove_pollutant_lock(city["cityName"], sensor["sensorId"], pollutant)


def train_city_sensors(city: dict, sensor: dict, pollutant: str) -> None:
    Thread(target=train_regression_model, args=(city, sensor, pollutant), daemon=True).start()
