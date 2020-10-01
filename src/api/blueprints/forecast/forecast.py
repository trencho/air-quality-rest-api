from datetime import datetime
from os import path
from pickle import load as pickle_load

from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response, request
from pandas import read_csv, to_datetime

from api.blueprints import train_city_sensors
from api.config.cache import cache
from definitions import HTTP_BAD_REQUEST, HTTP_NOT_FOUND, pollutants, DATA_EXTERNAL_PATH, MODELS_PATH
from preparation import check_city, check_sensor, calculate_nearest_sensor
from processing import closest_hour, current_hour, next_hour, recursive_forecast

forecast_blueprint = Blueprint('forecast', __name__)


def append_sensor_forecast_data(sensor, pollutant, forecast_value, forecast_results):
    sensor_position = sensor['position'].split(',')
    latitude, longitude = float(sensor_position[0]), float(sensor_position[1])
    forecast_results.append({
        'latitude': latitude,
        'longitude': longitude,
        pollutant: forecast_value
    })


@forecast_blueprint.route('/pollutants/<string:pollutant_name>/forecast', endpoint='forecast_all', methods=['GET'])
@forecast_blueprint.route('/pollutants/<string:pollutant_name>/cities/<string:city_name>/forecast',
                          endpoint='forecast_city', methods=['GET'])
@forecast_blueprint.route(
    '/pollutants/<string:pollutant_name>/cities/<string:city_name>/sensors/<string:sensor_id>/forecast',
    endpoint='forecast_city_sensor', methods=['GET'])
@swag_from('forecast_all.yml', endpoint='forecast.forecast_all', methods=['GET'])
@swag_from('forecast_city.yml', endpoint='forecast.forecast_city', methods=['GET'])
@swag_from('forecast_city_sensor.yml', endpoint='forecast.forecast_city_sensor', methods=['GET'])
def fetch_sensor_forecast(pollutant_name, city_name=None, sensor_id=None):
    if pollutant_name not in pollutants:
        message = 'Value cannot be predicted because the pollutant is not found or invalid.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)

    timestamp = retrieve_forecast_timestamp()
    if isinstance(timestamp, Response):
        return timestamp

    forecast_results = []
    if city_name is None:
        cities = cache.get('cities') or []
        sensors = cache.get('sensors') or {}
        for city in cities:
            for sensor in sensors[city['cityName']]:
                forecast_value = forecast_city_sensor(city, sensor, pollutant_name, timestamp)
                append_sensor_forecast_data(sensor, pollutant_name, forecast_value, forecast_results)

        return make_response(jsonify(forecast_results))

    city = check_city(city_name)
    if city is None:
        message = 'Value cannot be predicted because the city is not found or invalid.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)

    if sensor_id is None:
        sensors = cache.get('sensors') or {}
        for sensor in sensors[city['cityName']]:
            forecast_value = forecast_city_sensor(city, sensor, pollutant_name, timestamp)
            append_sensor_forecast_data(sensor, pollutant_name, forecast_value, forecast_results)

        return make_response(jsonify(forecast_results))

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Value cannot be predicted because the sensor is not found or inactive.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)

    forecast_value = forecast_city_sensor(city, sensor, pollutant_name, timestamp)

    append_sensor_forecast_data(sensor, pollutant_name, forecast_value, forecast_results)
    return make_response(jsonify(forecast_results))


@forecast_blueprint.route('/coordinates/<float:latitude>,<float:longitude>/forecast/', endpoint='coordinates_all',
                          methods=['GET'])
@forecast_blueprint.route(
    '/coordinates/<float:latitude>,<float:longitude>/pollutants/<string:pollutant_name>/forecast/',
    endpoint='coordinates_pollutant', methods=['GET'])
@swag_from('forecast_coordinates_all.yml', endpoint='forecast.coordinates_all', methods=['GET'])
@swag_from('forecast_coordinates_pollutant.yml', endpoint='forecast.coordinates_pollutant', methods=['GET'])
def fetch_coordinates_forecast(latitude, longitude, pollutant_name=None):
    coordinates = (latitude, longitude)
    sensor = calculate_nearest_sensor(coordinates)
    if sensor is None:
        message = 'Value cannot be predicted because the coordinates are far away from all available sensors.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)

    forecast_results = []
    timestamp = retrieve_forecast_timestamp()
    if pollutant_name is None:
        cities = cache.get('cities')
        for city in cities:
            if city['cityName'] == sensor['cityName']:
                forecast_result = {
                    'latitude': latitude,
                    'longitude': longitude
                }
                for pollutant in pollutants:
                    forecast_result[pollutant] = forecast_city_sensor(city, sensor, pollutant, timestamp)

                forecast_results.append(forecast_result)
                return make_response(jsonify(forecast_results))

    if pollutant_name not in pollutants:
        message = 'Value cannot be predicted because the pollutant is not found or invalid.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)

    cities = cache.get('cities')
    for city in cities:
        if city['cityName'] == sensor['cityName']:
            forecast_value = forecast_city_sensor(city, sensor, pollutant_name, timestamp)
            forecast_results.append({'latitude': latitude, 'longitude': longitude, pollutant_name: forecast_value})
            return make_response(jsonify(forecast_results))


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
def forecast_city_sensor(city, sensor, pollutant, timestamp):
    load_model = load_regression_model(city, sensor, pollutant)
    if load_model is None:
        return load_model

    model, model_features = load_model

    dataframe = read_csv(path.join(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId'], 'summary.csv'))
    dataframe.set_index(to_datetime(dataframe['time'], unit='s'), inplace=True)

    current_datetime = current_hour(datetime.now())
    date_time = datetime.fromtimestamp(timestamp)
    n_steps = (date_time - current_datetime).total_seconds() // 3600
    return recursive_forecast(dataframe[pollutant], sensor, model, model_features, n_steps).iloc[-1]


def retrieve_forecast_timestamp():
    next_hour_time = next_hour(datetime.now())
    next_hour_timestamp = int(datetime.timestamp(next_hour_time))
    timestamp = request.args.get('timestamp', default=next_hour_timestamp, type=int)
    if timestamp < next_hour_timestamp:
        message = ('Cannot forecast pollutant because the timestamp is in the past. Send a GET request to the history '
                   'endpoint for past values.')
        return make_response(jsonify(error_message=message), HTTP_BAD_REQUEST)

    return closest_hour(datetime.fromtimestamp(timestamp)).timestamp()
