from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response
from flask_api.status import HTTP_404_NOT_FOUND

from api.blueprints import fetch_dataframe
from api.config.cache import cache
from definitions import pollutants
from preparation import check_city, check_sensor

pollutants_blueprint = Blueprint('pollutants', __name__)


def fetch_measurements(dataframe):
    measurements = [{'name': pollutants[pollutant], 'value': pollutant}
                    for pollutant in pollutants if pollutant in dataframe.columns]

    return measurements


@pollutants_blueprint.route('/cities/<string:city_name>/sensors/<string:sensor_id>/pollutants/',
                            endpoint='pollutants', methods=['GET'])
@cache.memoize(timeout=3600)
@swag_from('pollutants.yml', endpoint='pollutants.pollutants', methods=['GET'])
def fetch_pollutant(city_name, sensor_id):
    city = check_city(city_name)
    if city is None:
        message = 'Cannot return available pollutants because the city is not found or invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Cannot return available pollutants because the sensor is not found or invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    dataframe = fetch_dataframe(city_name, sensor_id)
    if isinstance(dataframe, Response):
        return dataframe

    measurements = fetch_measurements(dataframe)
    return make_response(jsonify(measurements))
