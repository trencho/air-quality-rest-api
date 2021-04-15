from os import environ, makedirs, path

from pandas import DataFrame

from definitions import DATA_EXTERNAL_PATH, environment_variables
from preparation.location_data import fetch_locations
from .cache import cache
from .database import mongo

collections = ['summary', 'pollution', 'weather']


def check_environment_variables():
    for environment_variable in environment_variables:
        if environ.get(environment_variable) is None:
            print(f'The environment variable "{environment_variable}" is missing')
            exit(-1)


def fetch_collection(collection, collection_dir, sensor_id):
    db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id}, projection={'_id': False})))
    if not db_records.empty:
        makedirs(collection_dir, exist_ok=True)
        db_records.to_csv(path.join(collection_dir, f'{collection}.csv'), index=False)


def fetch_db_data():
    fetch_locations()
    cities = cache.get('cities') or []
    sensors = cache.get('sensors') or {}
    for city in cities:
        for sensor in sensors[city['cityName']]:
            for collection in collections:
                collection_dir = path.join(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId'])
                fetch_collection(collection, collection_dir, sensor['sensorId'])
