from os import environ, makedirs, path

from pandas import DataFrame

from definitions import DATA_EXTERNAL_PATH, environment_variables, collections
from preparation.location_data import fetch_locations
from .cache import cache
from .database import mongo


def check_environment_variables():
    for environment_variable in environment_variables:
        env = environ.get(environment_variable)
        if env is None:
            print(f'The environment variable "{environment_variable}" is missing')
            exit(-1)


def fetch_collection(collection, collection_dir, sensor_id):
    db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id}, projection={'_id': False})))
    if not db_records.empty:
        collection_path = path.join(collection_dir, f'{collection}.csv')
        db_records.to_csv(collection_path, index=False)


def fetch_db_data():
    fetch_locations()
    cities = cache.get('cities') or []
    sensors = cache.get('sensors') or {}
    for city in cities:
        for sensor in sensors[city['cityName']]:
            for collection in collections:
                collection_dir = path.join(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId'])
                if not path.exists(collection_dir):
                    makedirs(collection_dir)
                fetch_collection(collection, collection_dir, sensor['sensorId'])
