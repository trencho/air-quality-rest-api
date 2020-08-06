from datetime import datetime
from json import load as json_load
from os import environ, makedirs, path
from pickle import load as pickle_load
from threading import Thread

from flask import jsonify, make_response, Response
from pandas import DataFrame, read_csv
from requests import get as requests_get

from definitions import DATA_EXTERNAL_PATH, MODELS_PATH, HTTP_BAD_REQUEST, HTTP_NOT_FOUND, dark_sky_token_env_value
from modeling import train_regression_model
from preparation import fetch_pollution_data, fetch_weather_data
from processing import generate_time_features, encode_categorical_data, merge_air_quality_data


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


def forecast_sensor(sensor, start_time):
    url = 'https://api.darksky.net/forecast'
    params = 'exclude=currently,minutely,daily,alerts,flags&extend=hourly'
    dark_sky_env = environ[dark_sky_token_env_value]
    with open(dark_sky_env) as dark_sky_file:
        dark_sky_json = json_load(dark_sky_file)
    private_key = dark_sky_json['private_key']
    link = f'{url}/{private_key}/{sensor["position"]},{start_time}'

    weather_response = requests_get(url=link, params=params)
    try:
        weather_json = weather_response.json()
        hourly = weather_json['hourly']
        hourly_data = hourly['data']
        for hourly in hourly_data:
            if hourly['time'] == start_time:
                return hourly
    except (KeyError, ValueError):
        message = 'Cannot fetch forecast data for the given timestamp.'
        return make_response(jsonify(error_message=message), HTTP_BAD_REQUEST)

    return {}


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

    with open(path.join(MODELS_PATH, city['cityName'], sensor['sensorId'], pollutant, 'selected_features.txt'),
              'rb') as in_file:
        model_features = pickle_load(in_file)

    return model, model_features


def forecast_city_sensor(city, sensor, pollutant, timestamp):
    load_model = load_regression_model(city, sensor, pollutant)
    if isinstance(load_model, tuple):
        model, model_features = load_model
    elif isinstance(load_model, Response):
        return {}

    forecast_data = forecast_sensor(sensor, timestamp)
    date_time = datetime.fromtimestamp(timestamp)
    data = {'time': date_time}
    dataframe = DataFrame(data, index=[0])
    generate_time_features(dataframe)
    data.update(dataframe.to_dict('list'))
    for model_feature in model_features:
        if model_feature not in dataframe.columns:
            feature = forecast_data.get(model_feature)

            # Reject request that has bad or missing features
            if feature is None:
                message = ('Value cannot be predicted because of missing or unacceptable values. '
                           'All values must be present and of type float.')
                return make_response(jsonify(error_message=message, feature=model_feature), HTTP_BAD_REQUEST)

            data[model_feature] = feature

    dataframe = DataFrame(data, index=[0])[model_features]
    encode_categorical_data(dataframe)

    sensor_position = sensor['position'].split(',')
    latitude, longitude = float(sensor_position[0]), float(sensor_position[1])
    forecast_result = {
        'latitude': latitude,
        'longitude': longitude,
        'value': float(round(model.predict(dataframe)[0], 2))
    }

    return forecast_result


def current_hour(t):
    return t.replace(microsecond=0, second=0, minute=0, hour=t.hour)


def next_hour(t):
    return t.replace(microsecond=0, second=0, minute=0, hour=0 if t.hour == 23 else t.hour + 1,
                     day=t.day + 1 if t.hour == 23 else t.day)
