from os import makedirs, path

from flask import jsonify, make_response, Response
from pandas import DataFrame, read_csv
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from definitions import collections, DATA_PROCESSED_PATH, DATA_RAW_PATH
from preparation import fetch_dark_sky_data, fetch_open_weather_data, fetch_pollution_data
from processing import process_data
from processing.merge_data import merge_air_quality_data


@cache.memoize(timeout=3600)
def fetch_dataframe(city_name: str, sensor_id: str, collection: str) -> [DataFrame, Response]:
    try:
        return read_csv(path.join(DATA_PROCESSED_PATH, city_name, sensor_id, f'{collection}.csv'))
    except FileNotFoundError:
        message = 'Cannot return historical data because the data is missing for that city and sensor.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)


def create_data_paths(city_name: str, sensor_id: str) -> None:
    makedirs(path.join(DATA_RAW_PATH, city_name, sensor_id), exist_ok=True)
    makedirs(path.join(DATA_PROCESSED_PATH, city_name, sensor_id), exist_ok=True)


def fetch_city_data(city_name: str, sensor: dict) -> None:
    create_data_paths(city_name, sensor['sensorId'])

    fetch_dark_sky_data(city_name, sensor)
    fetch_open_weather_data(city_name, sensor)
    fetch_pollution_data(city_name, sensor)
    merge_air_quality_data(DATA_RAW_PATH, city_name, sensor['sensorId'])
    for collection in collections:
        process_data(city_name, sensor['sensorId'], collection)
