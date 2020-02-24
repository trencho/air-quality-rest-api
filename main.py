import json
import os
import pickle
from datetime import datetime
from threading import Thread

import pandas as pd
import requests
from flasgger import Swagger
from flask import Flask, jsonify, make_response, Response, request
from flask_cors import CORS
from flask_pymongo import PyMongo

from definitions import DATA_EXTERNAL_PATH, MODELS_PATH
from definitions import HTTP_BAD_REQUEST, HTTP_NOT_FOUND
from definitions import dark_sky_env_value, pulse_eco_env_value
from definitions import dummy_leap_year, seasons
from definitions import pollutants
from definitions import status_active
from modeling import train
from preparation import extract_pollution_json, extract_weather_json
from processing import merge
from processing.feature_generation import encode_categorical_data

app = Flask(__name__)
CORS(app)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/local'
mongo = PyMongo(app)
swagger = Swagger(app)


def check_city(city_name):
    cities = fetch_cities()
    for city in cities:
        if city['cityName'] == city_name:
            return city

    return None


def check_environment_variables():
    dark_sky_env = os.environ.get(dark_sky_env_value)
    if dark_sky_env is None:
        message = 'The environment variable \'' + dark_sky_env_value + '\' is not set'
        status_code = HTTP_BAD_REQUEST
        return make_response(jsonify(error_message=message), status_code)

    pulse_eco_env = os.environ.get(pulse_eco_env_value)
    if pulse_eco_env is None:
        message = 'The environment variable \'' + pulse_eco_env_value + '\' is not set'
        status_code = HTTP_BAD_REQUEST
        return make_response(jsonify(error_message=message), status_code)

    return dark_sky_env, pulse_eco_env


def check_sensor(city_name, sensor_id):
    sensors = fetch_sensors(city_name)
    for sensor in sensors:
        if sensor['sensorId'] == sensor_id:
            return sensor

    return None


def current_hour(t):
    return t.replace(microsecond=0, second=0, minute=0, hour=t.hour)


def fetch_city_data(dark_sky_env, pulse_eco_env, city_name, start_time, end_time):
    sensors = fetch_sensors(city_name)
    for sensor in sensors:
        threads = list()

        extract_weather_thread = Thread(target=extract_weather_json,
                                        args=(dark_sky_env, city_name, sensor, start_time, end_time))
        threads.append(extract_weather_thread)
        extract_weather_thread.start()

        extract_pollution_thread = Thread(target=extract_pollution_json,
                                          args=(pulse_eco_env, city_name, sensor, start_time, end_time))
        threads.append(extract_pollution_thread)
        extract_pollution_thread.start()

        Thread(target=merge_city_sensor_data, args=(threads, city_name, sensor['sensorId'])).start()


def forecast_sensor(dark_sky_env, sensor, start_time):
    url = 'https://api.darksky.net/forecast'
    params = 'exclude=currently,minutely,daily,alerts,flags&extend=hourly'
    with open(dark_sky_env) as dark_sky_file:
        dark_sky_json = json.load(dark_sky_file)
    private_key = dark_sky_json.get('private_key')
    link = url + '/' + private_key + '/' + sensor['position'] + ',' + str(start_time)

    with requests.get(url=link, params=params) as weather_response:
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

    return dict()


def fetch_cities():
    url = 'https://pulse.eco/rest/city/'
    with requests.get(url) as response:
        try:
            cities = response.json()
        except ValueError:
            return list()

    return cities


def fetch_sensors(city_name):
    url = 'https://' + city_name + '.pulse.eco/rest/sensor/'
    with requests.get(url) as response:
        try:
            sensors = response.json()
        except ValueError:
            return list()

    active_sensors = []
    for sensor in sensors:
        if sensor['status'] == status_active:
            active_sensors.append(sensor)

    return active_sensors


def forecast_city_sensor(dark_sky_env, city, sensor, pollutant, timestamp):
    load_model = load_regression_model(city, sensor['sensorId'], pollutant)
    if isinstance(load_model, tuple):
        model, model_features = load_model
    elif isinstance(load_model, Response):
        return load_model

    features_dict = dict()
    forecast_data = forecast_sensor(dark_sky_env, sensor, timestamp)
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

    features = pd.DataFrame(features_dict, index=[0])
    features = encode_categorical_data(features)

    forecast_result = dict()
    sensor_position = sensor['position'].split(',')
    latitude, longitude = float(sensor_position[0]), float(sensor_position[1])
    forecast_result['latitude'] = latitude
    forecast_result['longitude'] = longitude
    forecast_result['value'] = float(round(model.predict(features)[0], 2))

    return forecast_result


def next_hour(t):
    return t.replace(microsecond=0, second=0, minute=0, hour=t.hour + 1)


def load_regression_model(city, sensor, pollutant):
    if not os.path.exists(MODELS_PATH + '/' + city['cityName'] + '/' + sensor['sensorId'] + '/' + pollutant
                          + '/best_regression_model.pkl'):
        train_city_sensors(city, sensor, pollutant)
        message = 'Value cannot be predicted because the model is not trained yet. Try again later.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    with open(MODELS_PATH + '/' + city['cityName'] + '/' + sensor['sensorId'] + '/' + pollutant
              + '/best_regression_model.pkl', 'rb') as in_file:
        model = pickle.load(in_file)

    with open(MODELS_PATH + '/' + city['cityName'] + '/' + sensor['sensorId'] + '/' + pollutant
              + '/selected_features.txt', 'rb') as in_file:
        model_features = pickle.load(in_file)

    return model, model_features


def merge_city_sensor_data(threads, city_name, sensor_id):
    for thread in threads:
        thread.join()
    Thread(target=merge, args=(city_name, sensor_id)).start()


def train_city_sensors(city, sensor, pollutant):
    Thread(target=train, args=(city, sensor, pollutant)).start()


@app.route('/city/', methods=['GET'])
@app.route('/city/<string:city_name>/', methods=['GET'])
def fetch_city(city_name=None):
    if city_name is None:
        message = fetch_cities()
        return make_response(jsonify(message))

    city = check_city(city_name)
    if city is None:
        message = 'Cannot return data because the city is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    message = city
    return make_response(jsonify(message))


@app.route('/city/<string:city_name>/sensor/', methods=['GET'])
@app.route('/city/<string:city_name>/sensor/<string:sensor_id>/', methods=['GET'])
def fetch_city_sensor(city_name, sensor_id=None):
    city = check_city(city_name)
    if city is None:
        message = 'Cannot return data because the city is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    if sensor_id is None:
        message = fetch_sensors(city_name)
        return make_response(jsonify(message))

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Cannot return data because the sensor is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    message = sensor
    return make_response(jsonify(message))


@app.route('/fetch/', methods=['GET'])
@app.route('/fetch/<string:city_name>', methods=['GET'])
def fetch_data(city_name=None):
    check_env = check_environment_variables()
    if isinstance(check_env, tuple):
        dark_sky_env, pulse_eco_env = check_env
    elif isinstance(check_env, Response):
        return check_env

    current_datetime = current_hour(datetime.now())
    current_timestamp = int(datetime.timestamp(current_datetime))
    start_time = request.args.get('startTime', default=current_timestamp, type=int)

    next_hour_datetime = next_hour(current_datetime)
    next_hour_timestamp = int(datetime.timestamp(next_hour_datetime))
    end_time = request.args.get('endTime', default=next_hour_timestamp, type=int)

    if end_time <= start_time:
        message = 'Specify end timestamp larger than the current hour\'s timestamp.'
        status_code = HTTP_BAD_REQUEST
        return make_response(jsonify(error_message=message), status_code)

    if city_name is None:
        cities = fetch_cities()
        for city in cities:
            fetch_city_data(dark_sky_env, pulse_eco_env, city['cityName'], start_time, end_time)

        message = 'Fetched weather data from the Dark Sky API for all cities.'
        return make_response(jsonify(success=message))

    city = check_city(city_name)
    if city is None:
        message = 'Cannot fetch data because the city is missing or is invalid.'
        status_code = HTTP_BAD_REQUEST
        return make_response(jsonify(error_message=message), status_code)

    fetch_city_data(dark_sky_env, pulse_eco_env, city_name, start_time, end_time)

    message = 'Fetched weather data from the Dark Sky API for ' + city['siteName'] + '.'
    return make_response(jsonify(success=message))


@app.route('/forecast/pollutant/<pollutant_name>', methods=['GET'])
def forecast(pollutant_name):
    check_env = check_environment_variables()
    if isinstance(check_env, tuple):
        dark_sky_env, pulse_eco_env = check_env
    elif isinstance(check_env, Response):
        return check_env

    if pollutant_name not in pollutants:
        message = 'Value cannot be predicted because the pollutant is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    next_hour_time = next_hour(datetime.now())
    next_hour_timestamp = int(datetime.timestamp(next_hour_time))
    timestamp = request.args.get('timestamp', default=next_hour_timestamp, type=int)
    if timestamp < next_hour_timestamp:
        message = ('Cannot forecast pollutant because the timestamp is in the past. '
                   'Send a GET request to the history endpoint for past values.')
        status_code = HTTP_BAD_REQUEST
        return make_response(jsonify(error_message=message), status_code)

    city_name = request.args.get('cityName', default=None, type=str)
    sensor_id = request.args.get('sensorId', default=None, type=str)
    forecast_results = list()
    if city_name is None:
        if sensor_id is not None:
            message = 'Cannot forecast pollutant because the city is missing.'
            status_code = HTTP_BAD_REQUEST
            return make_response(jsonify(error_message=message), status_code)

        cities = fetch_cities()
        for city in cities:
            sensors = fetch_sensors(city['cityName'])
            for sensor in sensors:
                forecast_result = forecast_city_sensor(dark_sky_env, city, sensor, pollutant_name,
                                                       timestamp)
                if isinstance(forecast_result, Response):
                    return forecast_result

                forecast_results.append(forecast_result)

        return make_response(jsonify(forecast_results))

    city = check_city(city_name)
    if city is None:
        message = 'Value cannot be predicted because the city is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    if sensor_id is None:
        sensors = fetch_sensors(city['cityName'])
        for sensor in sensors:
            forecast_result = forecast_city_sensor(dark_sky_env, city, sensor, pollutant_name, timestamp)
            if isinstance(forecast_result, Response):
                return forecast_result

            forecast_results.append(forecast_result)

        return make_response(jsonify(forecast_results))

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Value cannot be predicted because the sensor is missing or is inactive.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    forecast_result = forecast_city_sensor(dark_sky_env, city, sensor, pollutant_name, timestamp)
    if isinstance(forecast_result, Response):
        return forecast_result

    forecast_results.append(forecast_result)

    return make_response(jsonify(forecast_results))


@app.route('/history/city/<string:city_name>/sensor/<string:sensor_id>/pollutant/', methods=['GET'])
@app.route('/history/city/<string:city_name>/sensor/<string:sensor_id>/pollutant/<pollutant_name>/', methods=['GET'])
def history(city_name, sensor_id, pollutant_name=None):
    city = check_city(city_name)
    if city is None:
        message = 'Cannot return historical data because the city is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Cannot return historical data because the sensor is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    dataframe = pd.read_csv(DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor_id + '/weather_pollution_report.csv')
    if pollutant_name is None:
        measurements = list()
        for pollutant in pollutants:
            if pollutant in dataframe.columns:
                measurement_dict = dict()
                measurement_dict['name'] = pollutants[pollutant]
                measurement_dict['value'] = pollutant
                measurements.append(measurement_dict)
        message = measurements
        return make_response(jsonify(message))

    if pollutant_name not in dataframe.columns:
        message = 'Cannot return historical data because the pollutant is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    dataframe['time'] = dataframe['time'] * 1000
    return make_response(dataframe[['time', pollutant_name]].to_json(orient='values'))


@app.route('/train', methods=['GET'])
def train_data():
    city_name = request.args.get('cityName', default=None, type=str)
    city = check_city(city_name)
    if city_name is not None and city is None:
        message = 'Data cannot be trained because the city is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    sensor_id = request.args.get('sensorId', default=None, type=str)
    if city is None and sensor_id is not None:
        message = 'Data cannot be trained because the city is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    pollutant_name = request.args.get('pollutant', default=None, type=str)
    if pollutant_name is not None and pollutant_name not in pollutants:
        message = 'Data cannot be trained because the pollutant is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    if city_name is None:
        cities = fetch_cities()
        for city in cities:
            sensors = fetch_sensors(city['cityName'])
            for sensor in sensors:
                if pollutant_name is None:
                    for pollutant in pollutants:
                        train_city_sensors(city, sensor, pollutant)
                else:
                    train_city_sensors(city, sensor, pollutant_name)
    else:
        if sensor_id is None:
            sensors = fetch_sensors(city['cityName'])
            for sensor in sensors:
                if pollutant_name is None:
                    for pollutant in pollutants:
                        train_city_sensors(city, sensor, pollutant)
                else:
                    train_city_sensors(city, sensor, pollutant_name)
        else:
            sensor = check_sensor(city_name, sensor_id)
            if sensor is None:
                message = 'Data cannot be trained because the sensor is missing or is invalid.'
                status_code = HTTP_NOT_FOUND
                return make_response(jsonify(error_message=message), status_code)

            if pollutant_name is None:
                for pollutant in pollutants:
                    train_city_sensors(city, sensor, pollutant)
            else:
                train_city_sensors(city, sensor, pollutant_name)

    message = 'Training initialized...'
    return make_response(jsonify(success=message))


if __name__ == '__main__':
    app.run(debug=True)
