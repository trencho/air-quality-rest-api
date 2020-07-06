from os import environ, makedirs, path
from threading import Thread

from pandas import DataFrame

from api.blueprints import fetch_cities, fetch_sensors
from definitions import DATA_EXTERNAL_PATH, environment_variables, collections
from .db import mongo


def check_environment_variables():
    for environment_variable in environment_variables:
        env = environ.get(environment_variable)
        if env is None:
            print(f'The environment variable "{environment_variable}" is missing')
            exit(-1)


def fetch_collection(collection, collection_dir, sensor_id):
    db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id})))
    if not db_records.empty:
        db_records.drop(columns='_id', inplace=True, errors='ignore')
        collection_path = path.join(collection_dir, f'{collection}_report.csv')
        db_records.to_csv(collection_path, index=False)


def fetch_db_data():
    cities = fetch_cities()
    for city in cities:
        sensors = fetch_sensors(city['cityName'])
        for sensor in sensors:
            for collection in collections:
                collection_dir = path.join(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId'])
                if not path.exists(collection_dir):
                    makedirs(collection_dir)
                Thread(target=fetch_collection, args=(collection, collection_dir, sensor['sensorId'])).start()
