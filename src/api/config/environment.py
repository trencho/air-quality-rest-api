from os import environ, makedirs, path

from pandas import DataFrame

from definitions import collections, DATA_EXTERNAL_PATH, DATA_PROCESSED_PATH, DATA_RAW_PATH, environment_variables, \
    MODELS_PATH, mongodb_connection, RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH
from .cache import cache
from .database import mongo
from .schedule import fetch_locations

system_paths = [
    DATA_EXTERNAL_PATH,
    DATA_PROCESSED_PATH,
    DATA_RAW_PATH,
    MODELS_PATH,
    RESULTS_ERRORS_PATH,
    RESULTS_PREDICTIONS_PATH
]


def check_environment_variables() -> None:
    for environment_variable in environment_variables:
        if environ.get(environment_variable) is None:
            print(f'The environment variable "{environment_variable}" is missing')
            exit(-1)


def fetch_collection(collection: str, city_name: str, sensor_id: str) -> None:
    collection_dir = path.join(DATA_RAW_PATH, city_name, sensor_id)
    db_records = DataFrame(
        list(mongo.db[collection].find({'sensorId': sensor_id}, projection={'_id': False, 'sensorId': False})))
    if not db_records.empty:
        makedirs(collection_dir, exist_ok=True)
        db_records.to_csv(path.join(collection_dir, f'{collection}.csv'), index=False)


def fetch_db_data() -> None:
    sensors = cache.get('sensors') or {}
    for city in cache.get('cities') or []:
        for sensor in sensors[city['cityName']]:
            for collection in collections:
                fetch_collection(collection, city['cityName'], sensor['sensorId'])


def fetch_data() -> None:
    init_system_paths()
    fetch_locations()
    if environ.get(mongodb_connection) is not None:
        fetch_db_data()


def init_system_paths() -> None:
    for system_path in system_paths:
        makedirs(system_path, exist_ok=True)
