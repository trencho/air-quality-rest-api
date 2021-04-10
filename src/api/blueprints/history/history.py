from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response, request
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from api.blueprints import fetch_dataframe
from preparation import check_city, check_sensor
from processing import current_hour

week_in_seconds = 604800

history_blueprint = Blueprint('history', __name__)


@history_blueprint.route(
    '/cities/<string:city_name>/sensors/<string:sensor_id>/pollutants/<string:pollutant_name>/history/',
    endpoint='pollutant_history', methods=['GET'])
@swag_from('history.yml', endpoint='history.pollutant_history', methods=['GET'])
def fetch_history(city_name, sensor_id, pollutant_name):
    timestamps = retrieve_history_timestamps()
    if isinstance(timestamps, Response):
        return timestamps
    start_time, end_time = timestamps

    city = check_city(city_name)
    if city is None:
        message = 'Cannot return historical data because the city is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Cannot return historical data because the sensor is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    dataframe = fetch_dataframe(city_name, sensor_id)
    if isinstance(dataframe, Response):
        return dataframe

    if pollutant_name not in dataframe.columns:
        message = 'Cannot return historical data because the pollutant is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    dataframe = dataframe.loc[end_time >= dataframe['time'] >= start_time]
    dataframe['time'] = dataframe['time'] * 1000

    history_results = dataframe[['time', pollutant_name]].to_json(orient='values')
    return make_response(history_results)


def retrieve_history_timestamps():
    current_datetime = current_hour(datetime.now())
    current_timestamp = int(datetime.timestamp(current_datetime))
    start_time = request.args.get('start_time', default=current_timestamp, type=int)
    end_time = request.args.get('end_time', default=current_timestamp, type=int)
    if start_time > end_time:
        message = 'Specify end timestamp larger than the current hour\'s timestamp.'
        return make_response(jsonify(error_message=message), HTTP_400_BAD_REQUEST)
    if end_time > start_time + week_in_seconds:
        message = 'Specify start and end time in one week range.'
        return make_response(jsonify(error_message=message), HTTP_400_BAD_REQUEST)

    return start_time, end_time
