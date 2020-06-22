from os import environ, makedirs, path
from threading import Thread

from pandas import DataFrame

from api.resources import fetch_cities, fetch_sensors
from definitions import DATA_EXTERNAL_PATH, environment_variables, collections
from preparation import save_dataframe
from .db import mongo


def check_environment_variables():
    for environment_variable in environment_variables:
        env = environ.get(environment_variable)
        if env is None:
            print('The environment variable \'' + environment_variable + '\' is missing')
            exit(-1)


def check_collection_path(collection_path):
    if not path.exists(collection_path):
        makedirs(collection_path)
        return False

    return True


def fetch_collection(collection, city_name, sensor_id):
    collection_path = path.join(DATA_EXTERNAL_PATH, city_name, sensor_id)
    if not check_collection_path(collection_path):
        db_records = DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id})))
        if not db_records.empty:
            save_dataframe(db_records, collection, collection_path, sensor_id)


def fetch_mongodb_data():
    cities = fetch_cities()
    for city in cities:
        sensors = fetch_sensors(city['cityName'])
        for sensor in sensors:
            for collection in collections:
                Thread(target=fetch_collection, args=(collection, city['cityName'], sensor['sensorId'])).start()
