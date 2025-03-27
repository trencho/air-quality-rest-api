from datetime import datetime
from json import dumps
from logging import getLogger
from math import inf
from os import cpu_count, environ, makedirs, remove
from pathlib import Path
from threading import Thread

from pandas import DataFrame, read_csv, Series, to_datetime
from pytz import UTC
from sklearn.model_selection import RandomizedSearchCV

from definitions import APP_ENV, DATA_PROCESSED_PATH, ENV_DEV, MODELS_PATH, POLLUTANTS, REGRESSION_MODELS, \
    RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH
from models import make_model
from models.base_regression_model import BaseRegressionModel
from processing import backward_elimination, current_hour, encode_categorical_data, generate_features, \
    fetch_summary_dataframe, value_scaling
from visualization import draw_errors, draw_predictions
from .process_results import save_errors, save_results

logger = getLogger(__name__)
LOCK_FILE = ".lock"


def previous_value_overwrite(dataframe: DataFrame) -> DataFrame:
    dataframe = dataframe.shift(periods=-1, axis=0)
    return dataframe.drop(dataframe.tail(1).index)


def split_dataframe(dataframe: DataFrame, target: str, selected_features: list = None) -> tuple:
    x = dataframe.drop(columns=POLLUTANTS, errors="ignore")
    x = value_scaling(x)
    y = dataframe[target]

    x = previous_value_overwrite(x)
    y = y.drop(y.tail(1).index)

    selected_features = backward_elimination(x, y) if selected_features is None else selected_features
    x = x[selected_features]

    return x, y


def save_selected_features(data_path: Path, selected_features: list) -> None:
    create_path(data_path)
    (data_path / "selected_features.json").write_text(dumps(selected_features))


def read_model(data_path: Path, model_name: str, error_type: str) -> tuple:
    dataframe_errors = read_csv(RESULTS_ERRORS_PATH / "data" / data_path / "error.csv")
    model = make_model(model_name)
    model.load(MODELS_PATH / data_path)
    return model, dataframe_errors.iloc[0][error_type]


def create_path(data_path: Path) -> None:
    makedirs(data_path, exist_ok=True)


def create_results_paths(data_path: Path) -> None:
    create_path(RESULTS_ERRORS_PATH / "data" / data_path)
    create_path(RESULTS_PREDICTIONS_PATH / "data" / data_path)


def check_pollutant_lock(data_path: str) -> bool:
    return (MODELS_PATH / data_path / LOCK_FILE).exists()


def create_pollutant_lock(data_path: str) -> None:
    create_path(MODELS_PATH / data_path)
    (MODELS_PATH / data_path / LOCK_FILE).write_text("")


def hyper_parameter_tuning(model: BaseRegressionModel, x_train: DataFrame, y_train: Series, data_path: Path) -> dict:
    model_cv = RandomizedSearchCV(estimator=model.reg, param_distributions=model.param_grid, n_iter=50,
                                  n_jobs=cpu_count() // 2, cv=5, random_state=42)
    model_cv.fit(x_train, y_train)

    if environ.get(APP_ENV, ENV_DEV) == ENV_DEV:
        (MODELS_PATH / data_path / type(model).__name__ / "HyperparameterOptimization.json").write_text(
            dumps(model_cv.best_params_))

    return model_cv.best_params_


def remove_pollutant_lock(data_path: Path) -> None:
    try:
        remove(MODELS_PATH / data_path / LOCK_FILE)
    except OSError:
        pass


def check_best_regression_model(data_path: Path) -> bool:
    try:
        model_dir = MODELS_PATH / data_path
        if not (files := list(model_dir.glob("*.mdl"))):
            return False

        last_modified = int(Path(files[0]).stat().st_mtime)
        three_months_in_seconds = 7889400
        if last_modified < int(datetime.timestamp(current_hour())) - three_months_in_seconds:
            remove(model_dir / files[0])
            return False

        return True
    except OSError:
        return False


def generate_regression_model(dataframe: DataFrame, city_name: str, sensor_id: str, pollutant: str) -> None:
    dataframe = dataframe.join(generate_features(dataframe[pollutant]), how="inner")
    dataframe = dataframe.dropna(axis="columns", how="all").dropna(axis="index", how="any")
    encode_categorical_data(dataframe)
    validation_split = len(dataframe.index) * 3 // 4

    train_dataframe = dataframe.iloc[:validation_split]
    x_train, y_train = split_dataframe(train_dataframe, pollutant)
    selected_features = x_train.columns.values.tolist()

    test_dataframe = dataframe.iloc[validation_split:]
    x_test, y_test = split_dataframe(test_dataframe, pollutant, selected_features)

    best_model_error = inf
    best_model = None
    for model_name in REGRESSION_MODELS:
        model_data_path = Path(city_name) / sensor_id / pollutant / model_name
        if (env_var := environ.get(APP_ENV, ENV_DEV)) == ENV_DEV and (
                MODELS_PATH / model_data_path / f"{model_name}.mdl").exists():
            model, model_error = read_model(model_data_path, model_name, "Mean Absolute Error")
            if model_error < best_model_error:
                best_model = model
                best_model_error = model_error
            continue

        try:
            model = setup_model(model_name, x_train, y_train, Path(city_name) / sensor_id / pollutant)
        except Exception:
            logger.error(
                f"Error occurred while training regression model for {city_name} - {sensor_id} - {pollutant} - "
                f"{model_name}", exc_info=True)
            continue

        if env_var == ENV_DEV:
            create_path(MODELS_PATH / model_data_path)
            model.save(MODELS_PATH / model_data_path)

        y_predicted = model.predict(x_test)

        results = DataFrame({"Actual": y_test, "Predicted": y_predicted}, x_test.index)
        create_results_paths(model_data_path)
        save_results(model_data_path, results)

        if (model_error := save_errors(model_data_path, y_test, y_predicted)) < best_model_error:
            best_model = model
            best_model_error = model_error

    if best_model is None:
        return

    save_selected_features(MODELS_PATH / city_name / sensor_id / pollutant, selected_features)
    x_train, y_train = split_dataframe(dataframe, pollutant, selected_features)
    try:
        best_model = setup_model(type(best_model).__name__, x_train, y_train,
                                 Path(city_name) / sensor_id / pollutant)
    except Exception:
        logger.error(f"Error occurred while training the best regression model for {city_name} - {sensor_id} - "
                     f"{pollutant} - {type(best_model).__name__}", exc_info=True)
    best_model.save(MODELS_PATH / city_name / sensor_id / pollutant)


def setup_model(model_name: str, x_train: DataFrame, y_train: Series, data_path: Path) -> BaseRegressionModel:
    model = make_model(model_name)
    params = hyper_parameter_tuning(model, x_train, y_train, data_path)
    model.set_params(**params)
    model.train(x_train, y_train)
    return model


def train_regression_model(city: dict, sensor: dict, pollutant: str) -> None:
    logger.info(f"Training model for {city['cityName']} - {sensor['sensorId']} - {pollutant}")
    data_path = Path(city["cityName"]) / sensor["sensorId"] / pollutant
    if check_best_regression_model(data_path) or check_pollutant_lock(data_path):
        logger.info(f"Skipped training model for {city['cityName']} - {sensor['sensorId']} - {pollutant}")
        return
    try:
        dataframe = fetch_summary_dataframe(DATA_PROCESSED_PATH / city["cityName"] / sensor["sensorId"],
                                            index_col="time")
        dataframe = dataframe.loc[dataframe.index <= to_datetime(datetime.now(UTC)).to_datetime64()]
        if pollutant in dataframe.columns:
            create_pollutant_lock(data_path)
            generate_regression_model(dataframe, city["cityName"], sensor["sensorId"], pollutant)
            draw_errors(city, sensor, pollutant)
            draw_predictions(city, sensor, pollutant)
        logger.info(f"Completed training model for {city['cityName']} - {sensor['sensorId']} - {pollutant}")
    except Exception:
        logger.error(f"Error occurred while training model for {city['cityName']} - "
                     f"{sensor['sensorId']} - {pollutant}", exc_info=True)
    finally:
        remove_pollutant_lock(data_path)


def train_city_sensors(city: dict, sensor: dict, pollutant: str) -> None:
    Thread(target=train_regression_model, args=(city, sensor, pollutant), daemon=True).start()
