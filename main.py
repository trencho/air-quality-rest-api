import json
import os
import urllib
from datetime import datetime, timedelta
from threading import Thread

import joblib
import pandas as pd
import pymongo
from flasgger import Swagger
from flask import Flask, jsonify, request

from definitions import HTTP_OK, HTTP_BAD_REQUEST, HTTP_NOT_FOUND
from definitions import MODELS_PATH, DATA_EXTERNAL_PATH
from definitions import cities, pollutants
from definitions import dark_sky_env_value, pulse_eco_env_value
from definitions import status_active
from preparation import extract_pollution_json, extract_weather_json
from src.modeling import train_model

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/local'
swagger = Swagger(app)
mongo = pymongo


def check_sensor(city_name, sensor_id):
    sensors = fetch_sensors(city_name)
    for sensor in sensors:
        if sensor['id'] == sensor_id and sensor['status'] == status_active:
            return sensor

    return None


def fetch_city_data(dark_sky_env, pulse_eco_env, city_name, start_time, end_time):
    sensors = fetch_sensors(city_name)
    for sensor in sensors:
        if sensor['status'] == 'ACTIVE':
            extract_weather_json(dark_sky_env, city_name, sensor['id'], sensor['position'], start_time, end_time)
            extract_pollution_json(pulse_eco_env, city_name, sensor['id'], start_time, end_time)


def fetch_sensors(city_name):
    url = 'https://' + city_name + '.pulse.eco/rest/sensor'
    with urllib.request.urlopen(url) as response:
        sensors = json.load(response)
    return sensors


def hour_rounder(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return t.replace(second=0, microsecond=0, minute=0, hour=t.hour) + timedelta(hours=t.minute // 30)


def response_error(message, status_code, info=None):
    response = jsonify(error_message=message)
    response.status_code = status_code
    if info is not None:
        response.info = info
    return response


def response_success(message, status_code, info=None):
    response = jsonify(message)
    response.status_code = status_code
    if info is not None:
        response.info = info
    return response


def train_city_sensors(city_name, pollutant, sensor=None):
    if sensor is not None:
        Thread(target=train_model.train, args=(city_name, sensor, pollutant)).start()
    else:
        sensors = fetch_sensors(city_name)
        for sensor in sensors:
            if sensor['status'] == 'ACTIVE':
                Thread(target=train_model.train, args=(city_name, sensor, pollutant)).start()


@app.route('/city', methods=['GET'])
def fetch_city():
    message = cities
    status_code = HTTP_OK
    return response_success(message, status_code)


@app.route('/fetch', methods=['GET'])
def fetch_data():
    dark_sky_env = os.environ.get(dark_sky_env_value)
    if dark_sky_env is None:
        message = 'Please set the environment variable \'DARK_SKY_CREDENTIALS\''
        status_code = HTTP_BAD_REQUEST
        return response_error(message, status_code)

    pulse_eco_env = os.environ.get(pulse_eco_env_value)
    if pulse_eco_env is None:
        message = 'Please set the environment variable \'PULSE_ECO_CREDENTIALS\''
        status_code = HTTP_BAD_REQUEST
        return response_error(message, status_code)

    current_hour = hour_rounder(datetime.now())

    start_time = request.args.get('startTime', default=None, type=int)
    if start_time is None:
        current_timestamp = datetime.timestamp(current_hour)
        start_time = current_timestamp

    end_time = request.args.get('endTime', default=None, type=int)
    if end_time is None:
        end_time = datetime.timestamp(current_hour)
    elif end_time < start_time:
        message = 'Specify end timestamp larger or equal to the current timestamp'
        status_code = HTTP_BAD_REQUEST
        return response_error(message, status_code)

    city_name = request.args.get('cityName', default=None, type=str)
    if city_name is not None:
        fetch_city_data(dark_sky_env, pulse_eco_env, city_name, start_time, end_time)
    else:
        for city_name in cities:
            fetch_city_data(dark_sky_env, pulse_eco_env, city_name, start_time, end_time)

    message = 'Fetched weather data from the Dark Sky API.'
    status_code = HTTP_OK
    return response_success(message, status_code)


@app.route('/forecast/city/<string:city_name>/sensor/<string:sensor_id>', methods=['GET'])
def forecast(city_name, sensor_id):
    if city_name not in cities:
        message = 'Record cannot be scored because the city is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return response_error(message, status_code)

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Record cannot be scored because the sensor is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return response_error(message, status_code)

    dataframe = pd.read_csv(DATA_EXTERNAL_PATH + '/combined/' + city_name + '/' + sensor_id + '/combined_report.csv')
    measurement = request.args.get('measurement', default=None, type=str)
    if measurement is not None and measurement not in dataframe.columns:
        message = 'Cannot return data because the measurement is missing.'
        status_code = HTTP_NOT_FOUND
        return response_error(message, status_code)

    if measurement is not None:
        dataframe['time'] = dataframe['time'] * 1000
        return dataframe[['time', measurement]].to_json(orient='values')
    else:
        message = dataframe.columns
        status_code = HTTP_OK
        return response_success(message, status_code)


@app.route('/predict/city/<string:city_name>/sensor/<string:sensor_id>', methods=['GET'])
def predict(city_name, sensor_id):
    if city_name not in cities:
        message = 'Record cannot be scored because the city is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return response_error(message, status_code)

    pollutant = request.args.get('pollutant', default=None, type=str)
    if pollutant not in pollutants:
        message = 'Record cannot be scored because the pollutant is missing or is invalid.'
        status_code = HTTP_NOT_FOUND
        return response_error(message, status_code)

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Record cannot be scored because the sensor is missing or is inactive.'
        status_code = HTTP_BAD_REQUEST
        return response_error(message, status_code)

    if not os.path.exists(
            MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/best_regression_model.pkl'):
        train_city_sensors(city_name, pollutant, sensor)
        message = 'Value cannot be predicted because the model is not trained. Try again later.'
        status_code = HTTP_NOT_FOUND
        return response_error(message, status_code)

    model = joblib.load(
        MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/best_regression_model.pkl')
    with open(MODELS_PATH + '/' + city_name + '/' + sensor_id + '/' + pollutant + '/selected_features.txt',
              'r') as in_file:
        model_features = in_file.read()
    features = []
    for model_feature in model_features:
        feature = request.args.get(model_feature, default=None, type=str)
        # Reject request that have bad or missing values
        if feature is None:
            message = ('Record cannot be scored because of missing or unacceptable values. '
                       'All values must be present and of type float.')
            status_code = HTTP_BAD_REQUEST
            return response_error(message, status_code, feature)
        else:
            features.append(feature)

    message = round(model.predict(features)[0])
    status_code = HTTP_OK
    return response_success(message, status_code)


@app.route('/city/<string:city_name>/sensor', methods=['GET'])
def fetch_city_sensor(city_name):
    message = fetch_sensors(city_name)
    status_code = HTTP_OK
    return response_success(message, status_code)


@app.route('/train', methods=['GET'])
def train():
    city_name = request.args.get('cityName', default=None, type=str)
    pollutant = request.args.get('pollutant', default=None, type=str)
    if (city_name is not None and city_name not in cities) or (pollutant is not None and pollutant not in pollutants):
        message = 'Record cannot be scored because the city or pollutant is missing.'
        status_code = HTTP_NOT_FOUND
        return response_error(message, status_code)

    sensor_id = request.args.get('sensorId', default=None, type=str)
    if city_name is not None:
        sensor = check_sensor(city_name, sensor_id)
        if sensor is None:
            message = 'Record cannot be scored because the sensor is missing or is inactive.'
            status_code = HTTP_BAD_REQUEST
            return response_error(message, status_code)

        train_city_sensors(city_name, pollutant, sensor)
    else:
        if sensor_id is not None:
            message = 'Record cannot be scored because the city is missing.'
            status_code = HTTP_BAD_REQUEST
            return response_error(message, status_code)

        for city_name in cities:
            train_city_sensors(city_name, pollutant)

    message = 'Training initialized...'
    status_code = HTTP_OK
    return response_success(message, status_code)


if __name__ == '__main__':
    app.run(debug=True)
