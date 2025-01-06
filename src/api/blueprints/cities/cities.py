from flasgger.utils import swag_from
from flask import Blueprint, jsonify, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from definitions import CACHE_TIMEOUTS
from preparation import check_city, read_cities

cities_blueprint = Blueprint("cities", __name__)


@cities_blueprint.get("/cities/", endpoint="cities")
@cities_blueprint.get("/cities/<string:city_name>/", endpoint="cities_name")
@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
@swag_from("cities.yml", endpoint="cities.cities", methods=["GET"])
@swag_from("cities_name.yml", endpoint="cities.cities_name", methods=["GET"])
def fetch_city(city_name: str = None) -> Response | tuple[Response, int]:
    if city_name is None:
        return jsonify(cache.get("cities") or read_cities())

    if (city := check_city(city_name)) is None:
        return jsonify(
            error_message="Cannot return data because the city is not found or is invalid."), HTTP_404_NOT_FOUND

    return jsonify(city)
