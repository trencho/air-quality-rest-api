from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response

from api.blueprints import check_city, check_sensor, fetch_dataframe
from definitions import HTTP_NOT_FOUND, pollutants

pollutant = Blueprint('pollutants', __name__)


def fetch_measurements(dataframe):
    measurements = []
    for pollutant in pollutants:
        if pollutant in dataframe.columns:
            measurement_dict = {
                'name': pollutants[pollutant],
                'value': pollutant
            }
            measurements.append(measurement_dict)

    return measurements


@pollutant.route('/cities/<string:city_name>/sensors/<string:sensor_id>/pollutants/', endpoint='pollutants_all',
                 methods=['GET'])
@swag_from('pollutants_all.yml', endpoint='pollutants.pollutants_all', methods=['GET'])
def fetch_pollutant(city_name, sensor_id):
    city = check_city(city_name)
    if city is None:
        message = 'Cannot return available pollutants because the city is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Cannot return available pollutants because the sensor is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    dataframe = fetch_dataframe(city_name, sensor_id)
    if isinstance(dataframe, Response):
        return make_response(jsonify({}))

    measurements = fetch_measurements(dataframe)
    return make_response(jsonify(measurements))