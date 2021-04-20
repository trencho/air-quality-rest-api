from os import makedirs, path

from flask import jsonify, make_response
from pandas import read_csv
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from definitions import DATA_EXTERNAL_PATH
from preparation import fetch_pollution_data, fetch_weather_data
from processing import merge_air_quality_data


@cache.memoize(timeout=3600)
def fetch_dataframe(city_name, sensor_id, data_type):
    try:
        return read_csv(path.join(DATA_EXTERNAL_PATH, city_name, sensor_id, f'{data_type}.csv'))
    except FileNotFoundError:
        message = 'Cannot return historical data because the data is missing for that city and sensor.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)


def create_data_path(city_name, sensor_id):
    data_path = path.join(DATA_EXTERNAL_PATH, city_name, sensor_id)
    makedirs(data_path, exist_ok=True)
    return data_path


def fetch_city_data(city_name, sensor):
    data_path = create_data_path(city_name, sensor['sensorId'])

    fetch_weather_data(city_name, sensor)
    fetch_pollution_data(city_name, sensor)
    if path.exists(path.join(data_path, 'weather.csv')) and path.exists(path.join(data_path, 'pollution.csv')):
        merge_air_quality_data(DATA_EXTERNAL_PATH, city_name, sensor['sensorId'])
