from datetime import datetime
from json import loads as json_loads

from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response, request
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from api.blueprints import fetch_dataframe
from api.config.cache import cache
from preparation import calculate_nearest_sensor, check_city, check_sensor
from processing import current_hour

history_blueprint = Blueprint('history', __name__)

data_types = ['pollution', 'weather']


@history_blueprint.route('/cities/<string:city_name>/sensors/<string:sensor_id>/history/<data_type>/',
                         endpoint='city_sensor', methods=['GET'])
@swag_from('history_city_sensor.yml', endpoint='history.city_sensor', methods=['GET'])
def fetch_city_sensor_history(city_name, sensor_id, data_type):
    if data_type not in data_types:
        message = 'Cannot return historical data because the data type is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

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

    return return_historical_data(city_name, sensor, data_type, start_time, end_time)


@history_blueprint.route('/coordinates/<float:latitude>,<float:longitude>/history/<data_type>/',
                         endpoint='coordinates', methods=['GET'])
@swag_from('history_coordinates.yml', endpoint='history.coordinates', methods=['GET'])
def fetch_coordinates_history(latitude, longitude, data_type):
    if data_type not in data_types:
        message = 'Cannot return historical data because the data type is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    timestamps = retrieve_history_timestamps()
    if isinstance(timestamps, Response):
        return timestamps
    start_time, end_time = timestamps

    coordinates = (latitude, longitude)
    sensor = calculate_nearest_sensor(coordinates)
    if sensor is None:
        message = 'Cannot return historical data because the coordinates are far away from all available sensors.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    return return_historical_data(sensor['cityName'], sensor, data_type, start_time, end_time)


def retrieve_history_timestamps():
    current_datetime = current_hour(datetime.now())
    current_timestamp = int(datetime.timestamp(current_datetime))
    week_in_seconds = 604800
    start_time = request.args.get('start_time', default=current_timestamp - week_in_seconds, type=int)
    end_time = request.args.get('end_time', default=current_timestamp, type=int)
    if start_time > end_time:
        message = 'Specify end timestamp larger than the current hour\'s timestamp.'
        return make_response(jsonify(error_message=message), HTTP_400_BAD_REQUEST)
    if end_time > start_time + week_in_seconds:
        message = 'Specify start and end time in one week range.'
        return make_response(jsonify(error_message=message), HTTP_400_BAD_REQUEST)

    return start_time, end_time


@cache.memoize(timeout=3600)
def return_historical_data(city_name, sensor, data_type, start_time, end_time):
    dataframe = fetch_dataframe(city_name, sensor['sensorId'], data_type)
    if isinstance(dataframe, Response):
        return dataframe

    dataframe = dataframe.loc[(dataframe['time'] >= start_time) & (dataframe['time'] <= end_time)]
    sensor_position = sensor['position'].split(',')
    latitude, longitude = float(sensor_position[0]), float(sensor_position[1])
    history_results = {'latitude': latitude, 'longitude': longitude, 'data': []}
    history_results['data'].extend(json_loads(dataframe.to_json(orient='records')))
    return make_response(history_results)
