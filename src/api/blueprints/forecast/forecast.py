from math import isnan
from os import path
from pickle import load as pickle_load

from flasgger import swag_from
from flask import Blueprint, jsonify, make_response
from pandas import read_csv, to_datetime
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from definitions import pollutants, DATA_EXTERNAL_PATH, MODELS_PATH
from modeling import train_city_sensors
from preparation import check_city, check_sensor, calculate_nearest_sensor
from processing.forecast_data import recursive_forecast

forecast_blueprint = Blueprint('forecast', __name__)


@forecast_blueprint.route('/cities/<string:city_name>/sensors/<string:sensor_id>/forecast',
                          endpoint='forecast_city_sensor', methods=['GET'])
@swag_from('forecast_city_sensor.yml', endpoint='forecast.forecast_city_sensor', methods=['GET'])
def fetch_city_sensor_forecast(city_name, sensor_id):
    city = check_city(city_name)
    if city is None:
        message = 'Value cannot be predicted because the city is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Value cannot be predicted because the sensor is not found or inactive.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    sensor_position = sensor['position'].split(',')
    latitude, longitude = float(sensor_position[0]), float(sensor_position[1])
    return return_forecast_results(latitude, longitude, city, sensor)


@forecast_blueprint.route('/coordinates/<float:latitude>,<float:longitude>/forecast/', endpoint='coordinates',
                          methods=['GET'])
@swag_from('forecast_coordinates.yml', endpoint='forecast.coordinates', methods=['GET'])
def fetch_coordinates_forecast(latitude, longitude):
    coordinates = (latitude, longitude)
    sensor = calculate_nearest_sensor(coordinates)
    if sensor is None:
        message = 'Value cannot be predicted because the coordinates are far away from all available sensors.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    cities = cache.get('cities')
    for city in cities:
        if city['cityName'] == sensor['cityName']:
            return return_forecast_results(latitude, longitude, city, sensor)


@cache.memoize(timeout=3600)
def load_regression_model(city, sensor, pollutant):
    if not path.exists(
            path.join(MODELS_PATH, city['cityName'], sensor['sensorId'], pollutant, 'best_regression_model.pkl')):
        train_city_sensors(city, sensor, pollutant)
        return None

    with open(path.join(MODELS_PATH, city['cityName'], sensor['sensorId'], pollutant, 'best_regression_model.pkl'),
              'rb') as in_file:
        model = pickle_load(in_file)

    with open(path.join(MODELS_PATH, city['cityName'], sensor['sensorId'], pollutant, 'selected_features.pkl'),
              'rb') as in_file:
        model_features = pickle_load(in_file)

    return model, model_features


@cache.memoize(timeout=3600)
def forecast_city_sensor(city, sensor, pollutant):
    load_model = load_regression_model(city, sensor, pollutant)
    if load_model is None:
        return load_model

    model, model_features = load_model

    dataframe = read_csv(path.join(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId'], 'summary.csv'),
                         index_col='time')
    dataframe.index = to_datetime(dataframe.index, unit='s')

    return recursive_forecast(dataframe[pollutant], city['cityName'], sensor['sensorId'], model, model_features)


@cache.memoize(timeout=3600)
def return_forecast_results(latitude, longitude, city, sensor):
    forecast_result = {}
    for pollutant in pollutants:
        predictions = forecast_city_sensor(city, sensor, pollutant)
        if predictions is None:
            continue

        for index, value in predictions.items():
            timestamp_dict = forecast_result.get(int(index.timestamp()), {})
            timestamp_dict.update({'time': int(index.timestamp()), pollutant: None if isnan(value) else value})
            forecast_result.update({int(index.timestamp()): timestamp_dict})

    forecast_results = {'latitude': latitude, 'longitude': longitude, 'data': []}
    forecast_results['data'].extend(forecast_result.values())
    return make_response(forecast_results)
