from os import environ

from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from api.config.database import mongo
from definitions import mongodb_connection
from preparation import calculate_nearest_sensor, check_city, check_sensor, read_cities
from processing import fetch_forecast_result

forecast_blueprint = Blueprint('forecast', __name__)


@forecast_blueprint.route('/cities/<string:city_name>/sensors/<string:sensor_id>/forecast/',
                          endpoint='forecast_city_sensor', methods=['GET'])
@cache.memoize(timeout=3600)
@swag_from('forecast_city_sensor.yml', endpoint='forecast.forecast_city_sensor', methods=['GET'])
def fetch_city_sensor_forecast(city_name: str, sensor_id: str) -> Response:
    if (city := check_city(city_name)) is None:
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
def fetch_coordinates_forecast(latitude: float, longitude: float) -> Response:
    if (sensor := calculate_nearest_sensor((latitude, longitude))) is None:
        message = 'Value cannot be predicted because the coordinates are far away from all available sensors.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    for city in cache.get('cities') or read_cities():
        if city['cityName'] == sensor['cityName']:
            return return_forecast_results(latitude, longitude, city, sensor)


def return_forecast_results(latitude: float, longitude: float, city: dict, sensor: dict) -> Response:
    forecast_results = {'latitude': latitude, 'longitude': longitude}
    if (mongodb_env := environ.get(mongodb_connection)) is not None:
        forecast_result = mongo.db['predictions'].find_one(
            {'cityName': city['cityName'], 'sensorId': sensor['sensorId']})
        if forecast_result is not None and forecast_result['data']:
            forecast_results['data'] = forecast_result['data']
            return make_response(forecast_results)

    forecast_result = fetch_forecast_result(city, sensor)
    forecast_results['data'] = list(forecast_result.values())
    if mongodb_env is not None:
        mongo.db['predictions'].replace_one({'cityName': city['cityName'], 'sensorId': sensor['sensorId']},
                                            {'data': list(forecast_result.values()),
                                             'cityName': city['cityName'], 'sensorId': sensor['sensorId']}, upsert=True)
    return make_response(forecast_results)
