import os
from threading import Thread

import pandas as pd

from api.resources import fetch_cities, fetch_sensors
from definitions import environment_variables, DATA_EXTERNAL_PATH, collections
from preparation.handle_data import save_dataframe
from .db import mongo


def check_environment_variables():
    for environment_variable in environment_variables:
        env = os.environ.get(environment_variable)
        if env is None:
            print('The environment variable \'' + environment_variable + '\' is not set')
            exit(-1)


def fetch_collection(collection, city_name, sensor_id):
    db_records = pd.DataFrame(list(mongo.db[collection].find({'sensorId': sensor_id})))
    path = DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor_id + '/' + collection + '_report.csv'
    save_dataframe(db_records, collection, path, sensor_id)


def fetch_mongodb_data():
    cities = fetch_cities()
    for city in cities:
        sensors = fetch_sensors(city['cityName'])
        for sensor in sensors:
            for collection in collections:
                Thread(target=fetch_collection, args=(collection, city['cityName'], sensor['sensorId'])).start()
