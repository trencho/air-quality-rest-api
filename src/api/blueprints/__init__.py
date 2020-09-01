from datetime import datetime
from os import makedirs, path
from pickle import load as pickle_load
from threading import Thread

from flask import jsonify, make_response, Response
from pandas import read_csv, to_datetime

from definitions import DATA_EXTERNAL_PATH, MODELS_PATH, HTTP_NOT_FOUND
from modeling import train_regression_model
from preparation import fetch_pollution_data, fetch_weather_data
from processing import current_hour, merge_air_quality_data, recursive_forecast


def fetch_dataframe(city_name, sensor_id):
    try:
        return read_csv(path.join(DATA_EXTERNAL_PATH, city_name, sensor_id, 'summary.csv'))
    except FileNotFoundError:
        message = 'Cannot return historical data because the data is missing for that city and sensor.'
        return make_response(jsonify(message))


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


def load_regression_model(city, sensor, pollutant):
    if not path.exists(
            path.join(MODELS_PATH, city['cityName'], sensor['sensorId'], pollutant, 'best_regression_model.pkl')):
        train_city_sensors(city, sensor, pollutant)
        message = 'Value cannot be predicted because the model is not trained yet. Try again later.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)

    with open(path.join(MODELS_PATH, city['cityName'], sensor['sensorId'], pollutant, 'best_regression_model.pkl'),
              'rb') as in_file:
        model = pickle_load(in_file)

    with open(path.join(MODELS_PATH, city['cityName'], sensor['sensorId'], pollutant, 'selected_features.pkl'),
              'rb') as in_file:
        model_features = pickle_load(in_file)

    return model, model_features


def forecast_city_sensor(city, sensor, pollutant, timestamp):
    load_model = load_regression_model(city, sensor, pollutant)
    if isinstance(load_model, tuple):
        model, model_features = load_model
    elif isinstance(load_model, Response):
        return None

    dataframe = read_csv(path.join(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId'], 'summary.csv'))
    dataframe.set_index(to_datetime(dataframe['time'], unit='s'), inplace=True)

    current_datetime = current_hour(datetime.now())
    date_time = datetime.fromtimestamp(timestamp)
    n_steps = (date_time - current_datetime).total_seconds() // 3600
    return recursive_forecast(dataframe[pollutant], model, model_features, n_steps).iloc[-1]
