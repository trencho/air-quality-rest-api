from os import makedirs, path
from threading import Thread

from flask import jsonify, make_response
from pandas import read_csv

from definitions import DATA_EXTERNAL_PATH, HTTP_NOT_FOUND
from modeling import train_regression_model
from preparation import fetch_pollution_data, fetch_weather_data
from processing import merge_air_quality_data


def fetch_dataframe(city_name, sensor_id):
    try:
        return read_csv(path.join(DATA_EXTERNAL_PATH, city_name, sensor_id, 'summary.csv'))
    except FileNotFoundError:
        message = 'Cannot return historical data because the data is missing for that city and sensor.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)


def create_data_path(city_name, sensor_id):
    if not path.exists(path.join(DATA_EXTERNAL_PATH, city_name, sensor_id)):
        makedirs(path.join(DATA_EXTERNAL_PATH, city_name, sensor_id))


def merge_city_sensor_data(threads, city_name, sensor_id):
    for thread in threads:
        thread.join()
    Thread(target=merge_air_quality_data, args=(city_name, sensor_id)).start()


def fetch_city_data(city_name, sensor, start_time, end_time):
    create_data_path(city_name, sensor['sensorId'])

    threads = []

    fetch_weather_thread = Thread(target=fetch_weather_data, args=(city_name, sensor, start_time, end_time))
    threads.append(fetch_weather_thread)
    fetch_weather_thread.start()

    fetch_pollution_thread = Thread(target=fetch_pollution_data, args=(city_name, sensor, start_time, end_time))
    threads.append(fetch_pollution_thread)
    fetch_pollution_thread.start()

    Thread(target=merge_city_sensor_data, args=(threads, city_name, sensor['sensorId'])).start()


def train_city_sensors(city, sensor, pollutant):
    Thread(target=train_regression_model, args=(city, sensor, pollutant)).start()
