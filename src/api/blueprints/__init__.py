from datetime import datetime
from json import load as json_load
from os import environ, makedirs, path
from pickle import load as pickle_load
from threading import Thread

from flask import jsonify, make_response, Response
from pandas import DataFrame, read_csv
from requests import get as requests_get

from definitions import DATA_EXTERNAL_PATH, MODELS_PATH, HTTP_BAD_REQUEST, HTTP_NOT_FOUND, status_active, \
    dark_sky_env_value, dummy_leap_year, seasons
from modeling import train_regression_model
from preparation import extract_pollution_json, extract_weather_json
from processing import encode_categorical_data, merge_air_quality_data


def fetch_dataframe(city_name, sensor_id):
    try:
        dataframe = read_csv(path.join(DATA_EXTERNAL_PATH, city_name, sensor_id, 'summary_report.csv'))
    except FileNotFoundError:
        message = 'Cannot return historical data because the data is missing for that city and sensor.'
        return make_response(jsonify(message))

    return dataframe


def fetch_cities():
    url = 'https://pulse.eco/rest/city/'
    with requests_get(url) as response:
        try:
            cities = response.json()
        except ValueError:
            return []

    return cities


def check_city(city_name):
    cities = fetch_cities()
    for city in cities:
        if city['cityName'] == city_name:
            return city

    return None


def fetch_sensors(city_name):
    url = 'https://' + city_name + '.pulse.eco/rest/sensor/'
    with requests_get(url) as response:
        try:
            sensors = response.json()
        except ValueError:
            return []

    active_sensors = []
    for sensor in sensors:
        if sensor['status'] == status_active:
            active_sensors.append(sensor)

    return active_sensors


def check_sensor(city_name, sensor_id):
    sensors = fetch_sensors(city_name)
    for sensor in sensors:
        if sensor['sensorId'] == sensor_id:
            return sensor

    return None


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

    extract_weather_thread = Thread(target=extract_weather_json, args=(city_name, sensor, start_time, end_time))
    threads.append(extract_weather_thread)
    extract_weather_thread.start()

    extract_pollution_thread = Thread(target=extract_pollution_json, args=(city_name, sensor, start_time, end_time))
    threads.append(extract_pollution_thread)
    extract_pollution_thread.start()

    Thread(target=merge_city_sensor_data, args=(threads, city_name, sensor['sensorId'])).start()


def forecast_sensor(sensor, start_time):
    url = 'https://api.darksky.net/forecast'
    params = 'exclude=currently,minutely,daily,alerts,flags&extend=hourly'
    dark_sky_env = environ.get(dark_sky_env_value)
    with open(dark_sky_env) as dark_sky_file:
        dark_sky_json = json_load(dark_sky_file)
    private_key = dark_sky_json.get('private_key')
    link = url + '/' + private_key + '/' + sensor['position'] + ',' + str(start_time)

    with requests_get(url=link, params=params) as weather_response:
        try:
            weather_json = weather_response.json()
            hourly = weather_json.get('hourly')
            hourly_data = hourly.get('data')
            for hourly in hourly_data:
                if hourly['time'] == start_time:
                    return hourly
        except ValueError:
            message = 'Cannot fetch forecast data for the given timestamp.'
            status_code = HTTP_BAD_REQUEST
            return make_response(jsonify(error_message=message), status_code)

    return {}


def train_city_sensors(city, sensor, pollutant):
    Thread(target=train_regression_model, args=(city, sensor, pollutant)).start()


def load_regression_model(city, sensor, pollutant):
    if not path.exists(
            path.join(MODELS_PATH, city['cityName'], sensor['sensorId'], pollutant, 'best_regression_model.pkl')):
        train_city_sensors(city, sensor, pollutant)
        message = 'Value cannot be predicted because the model is not trained yet. Try again later.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

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

    features_dict = {}
    forecast_data = forecast_sensor(sensor, timestamp)
    date_time = datetime.fromtimestamp(timestamp)
    for model_feature in model_features:
        if model_feature == 'hour':
            feature = date_time.hour
        elif model_feature == 'month':
            feature = date_time.month
        elif model_feature == 'dayOfWeek':
            feature = date_time.weekday()
        elif model_feature == 'dayOfYear':
            feature = date_time.timetuple().tm_yday
        elif model_feature == 'weekOfYear':
            feature = date_time.isocalendar()[1]
        elif model_feature == 'isWeekend':
            feature = 1 if date_time.weekday() in (5, 6) else 0
        elif model_feature == 'session':
            feature = 0 if 0 < date_time.hour <= 4 else 1 if 4 < date_time.hour <= 8 \
                else 2 if 8 < date_time.hour <= 12 else 3 if 12 < date_time.hour <= 16 \
                else 4 if 16 < date_time.hour <= 20 else 5
        elif model_feature == 'season':
            date = date_time.date().replace(year=dummy_leap_year)
            feature = next(season for season, (start, end) in seasons if start <= date <= end)
        else:
            feature = forecast_data.get(model_feature)

        # Reject request that have bad or missing features
        if feature is None:
            message = ('Value cannot be predicted because of missing or unacceptable values. '
                       'All values must be present and of type float.')
            status_code = HTTP_BAD_REQUEST
            return make_response(jsonify(error_message=message, feature=model_feature), status_code)

        features_dict.update({model_feature: feature})

    features = DataFrame(features_dict, index=[0])
    features = encode_categorical_data(features)

    sensor_position = sensor['position'].split(',')
    latitude, longitude = float(sensor_position[0]), float(sensor_position[1])
    forecast_result = {
        'latitude': latitude,
        'longitude': longitude,
        'value': float(round(model.predict(features)[0], 2))
    }

    return forecast_result


def current_hour(t):
    return t.replace(microsecond=0, second=0, minute=0, hour=t.hour)


def next_hour(t):
    return t.replace(microsecond=0, second=0, minute=0, hour=0 if t.hour == 23 else t.hour + 1,
                     day=t.day + 1 if t.hour == 23 else t.day)