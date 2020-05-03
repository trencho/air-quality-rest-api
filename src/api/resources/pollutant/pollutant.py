import pandas as pd
from flasgger import swag_from
from flask import Blueprint, jsonify, make_response

from api.resources import check_city, check_sensor
from definitions import HTTP_NOT_FOUND, DATA_EXTERNAL_PATH
from definitions import pollutants

pollutant = Blueprint('pollutant', __name__)


@pollutant.route('/cities/<string:city_name>/sensors/<string:sensor_id>/pollutants/', endpoint='pollutant',
                 methods=['GET'])
@swag_from('pollutant.yml', endpoint='pollutant.pollutant', methods=['GET'])
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

    dataframe = pd.read_csv(DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor_id + '/summary_report.csv')
    measurements = list()
    for pollutant in pollutants:
        if pollutant in dataframe.columns:
            measurement_dict = dict()
            measurement_dict['name'] = pollutants[pollutant]
            measurement_dict['value'] = pollutant
            measurements.append(measurement_dict)
    message = measurements
    return make_response(jsonify(message))
