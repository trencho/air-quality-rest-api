from os import makedirs, path

from flask import jsonify, make_response
from pandas import read_csv
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from definitions import collections, DATA_PROCESSED_PATH, DATA_RAW_PATH
from preparation import fetch_pollution_data, fetch_weather_data
from processing import merge_air_quality_data, process_data


@cache.memoize(timeout=3600)
def fetch_dataframe(city_name, sensor_id, collection):
    try:
        return read_csv(path.join(DATA_PROCESSED_PATH, city_name, sensor_id, f'{collection}.csv'))
    except FileNotFoundError:
        message = 'Cannot return historical data because the data is missing for that city and sensor.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)


def create_data_paths(city_name, sensor_id):
    makedirs(path.join(DATA_RAW_PATH, city_name, sensor_id), exist_ok=True)
    makedirs(path.join(DATA_PROCESSED_PATH, city_name, sensor_id), exist_ok=True)


def fetch_city_data(city_name, sensor):
    create_data_paths(city_name, sensor['sensorId'])

    fetch_weather_data(city_name, sensor)
    fetch_pollution_data(city_name, sensor)
    merge_air_quality_data(DATA_RAW_PATH, city_name, sensor['sensorId'])
    for collection in collections:
        process_data(city_name, sensor['sensorId'], collection)
