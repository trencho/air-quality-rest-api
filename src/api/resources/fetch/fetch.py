from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response, request

from api import check_city, check_environment_variables, fetch_cities, fetch_city_data, next_hour
from definitions import HTTP_BAD_REQUEST

fetch = Blueprint('fetch', __name__)


def current_hour(t):
    return t.replace(microsecond=0, second=0, minute=0, hour=t.hour)


@fetch.route('/fetch/', endpoint='fetch_all', methods=['GET'])
@fetch.route('/cities/<string:city_name>/fetch/', endpoint='fetch_city', methods=['GET'])
@swag_from('fetch_all.yml', endpoint='fetch.fetch_all', methods=['GET'])
@swag_from('fetch_city.yml', endpoint='fetch.fetch_city', methods=['GET'])
def fetch_data(city_name=None):
    check_env = check_environment_variables()
    if isinstance(check_env, tuple):
        dark_sky_env, pulse_eco_env = check_env
    elif isinstance(check_env, Response):
        return check_env

    current_datetime = current_hour(datetime.now())
    current_timestamp = int(datetime.timestamp(current_datetime))
    start_time = request.args.get('startTime', default=current_timestamp, type=int)

    next_hour_datetime = next_hour(current_datetime)
    next_hour_timestamp = int(datetime.timestamp(next_hour_datetime))
    end_time = request.args.get('endTime', default=next_hour_timestamp, type=int)

    if end_time <= start_time:
        message = 'Specify end timestamp larger than the current hour\'s timestamp.'
        status_code = HTTP_BAD_REQUEST
        return make_response(jsonify(error_message=message), status_code)

    if city_name is None:
        cities = fetch_cities()
        for city in cities:
            fetch_city_data(dark_sky_env, pulse_eco_env, city['cityName'], start_time, end_time)

        message = 'Fetched weather data from the Dark Sky API for all cities.'
        return make_response(jsonify(success=message))

    city = check_city(city_name)
    if city is None:
        message = 'Cannot fetch data because the city is either missing or invalid.'
        status_code = HTTP_BAD_REQUEST
        return make_response(jsonify(error_message=message), status_code)

    fetch_city_data(dark_sky_env, pulse_eco_env, city_name, start_time, end_time)

    message = 'Fetched weather data from the Dark Sky API for ' + city['siteName'] + '.'
    return make_response(jsonify(success=message))
