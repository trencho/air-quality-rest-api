from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.blueprints import fetch_dataframe
from api.config.cache import cache
from definitions import pollutants
from preparation import calculate_nearest_sensor, check_city, check_sensor

pollutants_blueprint = Blueprint('pollutants', __name__)


@cache.memoize(timeout=3600)
def fetch_measurements(city_name, sensor_id):
    dataframe = fetch_dataframe(city_name, sensor_id, 'pollution')
    if isinstance(dataframe, Response):
        return dataframe

    measurements = [{'name': pollutants[pollutant], 'value': pollutant}
                    for pollutant in pollutants if pollutant in dataframe.columns]

    return make_response(jsonify(measurements))


@pollutants_blueprint.route('/cities/<string:city_name>/sensors/<string:sensor_id>/pollutants/', endpoint='city_sensor',
                            methods=['GET'])
@cache.memoize(timeout=3600)
@swag_from('pollutants_city_sensor.yml', endpoint='pollutants.city_sensor', methods=['GET'])
def fetch_city_sensor_pollutants(city_name, sensor_id):
    city = check_city(city_name)
    if city is None:
        message = 'Cannot return available pollutants because the city is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Cannot return available pollutants because the sensor is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    return fetch_measurements(sensor['cityName'], sensor['sensorId'])


@pollutants_blueprint.route('/coordinates/<float:latitude>,<float:longitude>/pollutants/', endpoint='coordinates',
                            methods=['GET'])
@swag_from('pollutants_coordinates.yml', endpoint='pollutants.coordinates', methods=['GET'])
def fetch_coordinates_pollutants(latitude, longitude):
    coordinates = (latitude, longitude)
    sensor = calculate_nearest_sensor(coordinates)
    if sensor is None:
        message = 'Cannot return available pollutants because the coordinates are far away from all available sensors.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    return fetch_measurements(sensor['cityName'], sensor['sensorId'])
