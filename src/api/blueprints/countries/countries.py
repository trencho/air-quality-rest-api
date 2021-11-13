from flasgger.utils import swag_from
from flask import Blueprint, jsonify, make_response, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from preparation import check_country, read_countries

countries_blueprint = Blueprint('countries', __name__)


@countries_blueprint.route('/countries/', endpoint='countries', methods=['GET'])
@countries_blueprint.route('/countries/<string:country_code>/', endpoint='country_code', methods=['GET'])
@cache.memoize(timeout=3600)
@swag_from('countries.yml', endpoint='countries.countries', methods=['GET'])
@swag_from('countries_code.yml', endpoint='countries.countries_code', methods=['GET'])
def fetch_country(country_code: str = None) -> Response:
    if country_code is None:
        return make_response(jsonify(cache.get('countries') or read_countries()))

    if (country := check_country(country_code)) is None:
        message = 'Cannot return data because the country is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    return make_response(country)
