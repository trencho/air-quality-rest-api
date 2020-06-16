from flasgger.utils import swag_from
from flask import Blueprint, jsonify, make_response

from api.resources import check_city, fetch_cities
from definitions import HTTP_NOT_FOUND

cities = Blueprint('cities', __name__)


@cities.route('/cities/', endpoint='city_all', methods=['GET'])
@cities.route('/cities/<string:city_name>/', endpoint='city_name', methods=['GET'])
@swag_from('city_all.yml', endpoint='cities.city_all', methods=['GET'])
@swag_from('city_name.yml', endpoint='cities.city_name', methods=['GET'])
def fetch_city(city_name=None):
    if city_name is None:
        message = fetch_cities()
        return make_response(jsonify(message))

    city = check_city(city_name)
    if city is None:
        message = 'Cannot return data because the city is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    return make_response(jsonify(city))
