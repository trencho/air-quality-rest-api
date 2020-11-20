from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, request
from flask_api.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from api.blueprints import fetch_city_data
from api.config.cache import cache
from preparation import check_city, check_sensor
from processing import current_hour, next_hour

fetch_blueprint = Blueprint('fetch', __name__)


@fetch_blueprint.route('/fetch/', endpoint='fetch_all', methods=['GET'])
@fetch_blueprint.route('/cities/<string:city_name>/fetch/', endpoint='fetch_city', methods=['GET'])
@fetch_blueprint.route('/cities/<string:city_name>/sensors/<string:sensor_id>/fetch/', endpoint='fetch_city_sensor',
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
        return make_response(jsonify(error_message=message), HTTP_400_BAD_REQUEST)

    if city_name is None:
        cities = cache.get('cities') or []
        sensors = cache.get('sensors') or {}
        for city in cities:
            for sensor in sensors[city['cityName']]:
                fetch_city_data(city['cityName'], sensor, start_time, end_time)

        message = 'Fetched weather and pollution data from the external APIs for all cities.'
        return make_response(jsonify(success=message))

    city = check_city(city_name)
    if city is None:
        message = 'Cannot fetch data because the city is not found or invalid.'
        return make_response(jsonify(error_message=message), HTTP_400_BAD_REQUEST)

    if sensor_id is None:
        sensors = cache.get('sensors') or {}
        for sensor in sensors[city['cityName']]:
            fetch_city_data(city_name, sensor, start_time, end_time)

        message = ('Started the operation to fetch weather and pollution data from the external APIs for '
                   f'{city["siteName"]} and all active sensors.')
        return make_response(jsonify(success=message))
    else:
        sensor = check_sensor(city_name, sensor_id)
        if sensor is None:
            message = 'Data cannot be trained because the sensor is not found or invalid.'
            return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

        fetch_city_data(city_name, sensor, start_time, end_time)

        message = ('Started the operation to fetch weather and pollution data from the external APIs for '
                   f'{city["siteName"]} and {sensor["description"]}.')
        return make_response(jsonify(success=message))
