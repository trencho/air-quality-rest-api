from flasgger.utils import swag_from
from flask import Blueprint, jsonify, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from preparation import check_country, read_countries

countries_blueprint = Blueprint("countries", __name__)


@countries_blueprint.get("/countries/", endpoint="countries")
@countries_blueprint.get("/countries/<string:country_code>/", endpoint="countries_code")
@cache.memoize(timeout=3600)
@swag_from("countries.yml", endpoint="countries.countries", methods=["GET"])
@swag_from("countries_code.yml", endpoint="countries.countries_code", methods=["GET"])
def fetch_country(country_code: str = None) -> Response | tuple[Response, int]:
    if country_code is None:
        return jsonify(cache.get("countries") or read_countries())

    if (country := check_country(country_code)) is None:
        return jsonify(
            error_message="Cannot return data because the country is not found or is invalid."), HTTP_404_NOT_FOUND

    return jsonify(country)
