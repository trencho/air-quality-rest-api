import pandas as pd
from flasgger import swag_from
from flask import Blueprint, jsonify, make_response

from api import check_city, check_sensor
from definitions import HTTP_NOT_FOUND, DATA_EXTERNAL_PATH

history = Blueprint('history', __name__)


@history.route('/cities/<string:city_name>/sensors/<string:sensor_id>/pollutants/<string:pollutant_name>/history/',
               endpoint='history_pollutant', methods=['GET'])
@swag_from('history.yml', endpoint='history.history_pollutant', methods=['GET'])
def history_pollutant(city_name, sensor_id, pollutant_name):
    city = check_city(city_name)
    if city is None:
        message = 'Cannot return historical data because the city is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Cannot return historical data because the sensor is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    dataframe = pd.read_csv(DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor_id + '/weather_pollution_report.csv')
    if pollutant_name not in dataframe.columns:
        message = 'Cannot return historical data because the pollutant is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    dataframe['time'] = dataframe['time'] * 1000
    history_result = dataframe[['time', pollutant_name]].to_json(orient='values')
    return make_response(history_result)
