from os import environ, makedirs, path

from flask_pymongo import ASCENDING
from pandas import DataFrame

from definitions import collections, DATA_EXTERNAL_PATH, DATA_PROCESSED_PATH, DATA_RAW_PATH, environment_variables, \
    MODELS_PATH, mongodb_connection, RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH
from .cache import cache
from .database import mongo
from .schedule import fetch_locations

__all__ = [
    DATA_EXTERNAL_PATH,
    DATA_PROCESSED_PATH,
    DATA_RAW_PATH,
    MODELS_PATH,
    RESULTS_ERRORS_PATH,
    RESULTS_PREDICTIONS_PATH
]


def check_environment_variables():
    for environment_variable in environment_variables:
        if environ.get(environment_variable) is None:
            print(f'The environment variable "{environment_variable}" is missing')
            exit(-1)


def fetch_collection(collection, city_name, sensor_id):
    collection_dir = path.join(DATA_RAW_PATH, city_name, sensor_id)
    mongo.db[collection].create_index([('sensorId', ASCENDING)])
    db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id}, projection={'_id': False})))
    if not db_records.empty:
        makedirs(collection_dir, exist_ok=True)
        db_records.to_csv(path.join(collection_dir, f'{collection}.csv'), index=False)


def fetch_db_data():
    cities = cache.get('cities') or []
    sensors = cache.get('sensors') or {}
    for city in cities:
        for sensor in sensors[city['cityName']]:
            for collection in collections:
                fetch_collection(collection, city['cityName'], sensor['sensorId'])


def fetch_data():
    init_system_paths()
    fetch_locations()
    if environ.get(mongodb_connection) is not None:
        fetch_db_data()


def init_system_paths():
    for system_path in __all__:
        makedirs(system_path, exist_ok=True)
