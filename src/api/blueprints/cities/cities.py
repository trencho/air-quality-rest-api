from flasgger.utils import swag_from
from flask import Blueprint, jsonify, make_response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from preparation import check_city

cities_blueprint = Blueprint('cities', __name__)


@cities_blueprint.route('/cities/', endpoint='cities', methods=['GET'])
@cities_blueprint.route('/cities/<string:city_name>/', endpoint='cities_name', methods=['GET'])
@cache.memoize(timeout=3600)
@swag_from('cities.yml', endpoint='cities.cities', methods=['GET'])
@swag_from('cities_name.yml', endpoint='cities.cities_name', methods=['GET'])
def fetch_city(city_name=None):
    if city_name is None:
        return make_response(jsonify(cache.get('cities') or []))

    city = check_city(city_name)
    if city is None:
        message = 'Cannot return data because the city is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    return make_response(jsonify(city))
