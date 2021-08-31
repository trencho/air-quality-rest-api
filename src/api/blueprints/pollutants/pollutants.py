from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.blueprints import fetch_dataframe
from api.config.cache import cache
from definitions import pollutants
from preparation import calculate_nearest_sensor, check_city, check_sensor

pollutants_blueprint = Blueprint('pollutants', __name__)


@cache.memoize(timeout=3600)
def fetch_measurements(city_name: str, sensor_id: str) -> Response:
    if isinstance(dataframe := fetch_dataframe(city_name, sensor_id, 'pollution'), Response):
        return dataframe

    measurements = [{'name': pollutants[pollutant], 'value': pollutant}
                    for pollutant in pollutants if pollutant in dataframe.columns]

    return make_response(jsonify(measurements))


@pollutants_blueprint.route('/cities/<string:city_name>/sensors/<string:sensor_id>/pollutants/', endpoint='city_sensor',
                            methods=['GET'])
@cache.memoize(timeout=3600)
@swag_from('pollutants_city_sensor.yml', endpoint='pollutants.city_sensor', methods=['GET'])
def fetch_city_sensor_pollutants(city_name: str, sensor_id: str) -> Response:
    if check_city(city_name) is None:
        message = 'Cannot return available pollutants because the city is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    if (sensor := check_sensor(city_name, sensor_id)) is None:
        message = 'Cannot return available pollutants because the sensor is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    return fetch_measurements(sensor['cityName'], sensor['sensorId'])


@pollutants_blueprint.route('/coordinates/<float:latitude>,<float:longitude>/pollutants/', endpoint='coordinates',
                            methods=['GET'])
@swag_from('pollutants_coordinates.yml', endpoint='pollutants.coordinates', methods=['GET'])
def fetch_coordinates_pollutants(latitude: float, longitude: float) -> Response:
    coordinates = (latitude, longitude)
    if (sensor := calculate_nearest_sensor(coordinates)) is None:
        message = 'Cannot return available pollutants because the coordinates are far away from all available sensors.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    return fetch_measurements(sensor['cityName'], sensor['sensorId'])
