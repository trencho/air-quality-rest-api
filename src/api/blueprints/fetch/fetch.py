from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, request

from api.blueprints import check_city, check_sensor, current_hour, fetch_cities, fetch_city_data, fetch_sensors, \
    next_hour
from definitions import HTTP_BAD_REQUEST, HTTP_NOT_FOUND

fetch = Blueprint('fetch', __name__)


@fetch.route('/fetch/', endpoint='fetch_all', methods=['GET'])
@fetch.route('/cities/<string:city_name>/fetch/', endpoint='fetch_city', methods=['GET'])
@fetch.route('/cities/<string:city_name>/sensors/<string:sensor_id>/fetch/', endpoint='fetch_city_sensor',
             methods=['GET'])
@swag_from('fetch_all.yml', endpoint='fetch.fetch_all', methods=['GET'])
@swag_from('fetch_city.yml', endpoint='fetch.fetch_city', methods=['GET'])
@swag_from('fetch_city_sensor.yml', endpoint='fetch.fetch_city_sensor', methods=['GET'])
def fetch_data(city_name=None, sensor_id=None):
    current_datetime = current_hour(datetime.now())
    current_timestamp = int(datetime.timestamp(current_datetime))
    start_time = request.args.get('start_time', default=current_timestamp, type=int)

    next_hour_datetime = next_hour(current_datetime)
    next_hour_timestamp = int(datetime.timestamp(next_hour_datetime))
    end_time = request.args.get('end_time', default=next_hour_timestamp, type=int)

    if end_time <= start_time:
        message = 'Specify end timestamp larger than the current hour\'s timestamp.'
        status_code = HTTP_BAD_REQUEST
        return make_response(jsonify(error_message=message), status_code)

    if city_name is None:
        cities = fetch_cities()
        for city in cities:
            sensors = fetch_sensors(city['cityName'])
            for sensor in sensors:
                fetch_city_data(city['cityName'], sensor, start_time, end_time)

        message = 'Fetched weather and pollution data from the external APIs for all cities.'
        return make_response(jsonify(success=message))

    city = check_city(city_name)
    if city is None:
        message = 'Cannot fetch data because the city is either missing or invalid.'
        status_code = HTTP_BAD_REQUEST
        return make_response(jsonify(error_message=message), status_code)

    if sensor_id is None:
        sensors = fetch_sensors(city['cityName'])
        for sensor in sensors:
            fetch_city_data(city_name, sensor, start_time, end_time)

        message = ('Started the operation to fetch weather and pollution data from the external APIs for '
                   + city['siteName'] + ' and all active sensors.')
        return make_response(jsonify(success=message))
    else:
        sensor = check_sensor(city_name, sensor_id)
        if sensor is None:
            message = 'Data cannot be trained because the sensor is either missing or invalid.'
            status_code = HTTP_NOT_FOUND
            return make_response(jsonify(error_message=message), status_code)

        fetch_city_data(city_name, sensor, start_time, end_time)

        message = ('Started the operation to fetch weather and pollution data from the external APIs for '
                   + city['siteName'] + ' and ' + sensor['description'] + '.')
        return make_response(jsonify(success=message))
