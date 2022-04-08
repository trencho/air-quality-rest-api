from os import environ, makedirs, path

from pandas import DataFrame

from definitions import collections, DATA_EXTERNAL_PATH, DATA_PROCESSED_PATH, DATA_RAW_PATH, environment_variables, \
    LOG_PATH, MODELS_PATH, mongodb_connection, RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH
from preparation import read_cities, read_sensors
from processing import find_missing_data, read_csv_in_chunks
from .database import mongo
from .logger import log
from .schedule import fetch_locations

system_paths = [
    DATA_EXTERNAL_PATH,
    DATA_PROCESSED_PATH,
    DATA_RAW_PATH,
    LOG_PATH,
    MODELS_PATH,
    RESULTS_ERRORS_PATH,
    RESULTS_PREDICTIONS_PATH
]


def check_environment_variables() -> None:
    for environment_variable in environment_variables:
        if environ.get(environment_variable) is None:
            log.error(f'The environment variable "{environment_variable}" is missing')
            exit(-1)


def fetch_collection(collection: str, city_name: str, sensor_id: str) -> None:
    collection_dir = path.join(DATA_RAW_PATH, city_name, sensor_id)
    db_records = DataFrame(
        list(mongo.db[collection].find({'sensorId': sensor_id}, projection={'_id': False, 'sensorId': False})))
    if len(db_records.index) > 0:
        makedirs(collection_dir, exist_ok=True)
        collection_path = path.join(collection_dir, f'{collection}.csv')
        if path.exists(collection_path):
            db_records = find_missing_data(db_records, read_csv_in_chunks(collection_path), 'time')
        db_records.to_csv(collection_path, header=not path.exists(collection_path), index=False, mode='a')


def fetch_db_data() -> None:
    for city in read_cities():
        for sensor in read_sensors(city['cityName']):
            for collection in collections:
                fetch_collection(collection, city['cityName'], sensor['sensorId'])


def fetch_data() -> None:
    fetch_locations()
    if environ.get(mongodb_connection) is not None:
        fetch_db_data()


def init_system_paths() -> None:
    for system_path in system_paths:
        makedirs(system_path, exist_ok=True)
