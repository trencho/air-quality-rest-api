from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, jsonify, request, Response
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from api.blueprints import fetch_city_data
from api.config.cache import cache
from preparation import check_city, check_sensor, read_cities, read_sensors
from processing import current_hour, next_hour

fetch_blueprint = Blueprint("fetch", __name__)


@fetch_blueprint.get("/fetch/", endpoint="fetch_all")
@fetch_blueprint.get("/cities/<string:city_name>/fetch/", endpoint="fetch_city")
@fetch_blueprint.get("/cities/<string:city_name>/sensors/<string:sensor_id>/fetch/", endpoint="fetch_city_sensor")
@swag_from("fetch_all.yml", endpoint="fetch.fetch_all", methods=["GET"])
@swag_from("fetch_city.yml", endpoint="fetch.fetch_city", methods=["GET"])
@swag_from("fetch_city_sensor.yml", endpoint="fetch.fetch_city_sensor", methods=["GET"])
def fetch_data(city_name: str = None, sensor_id: str = None) -> Response | tuple[Response, int]:
    current_datetime = current_hour()
    current_timestamp = int(datetime.timestamp(current_datetime))
    start_time = request.args.get("start_time", default=current_timestamp, type=int)

    next_hour_datetime = next_hour(current_datetime)
    next_hour_timestamp = int(datetime.timestamp(next_hour_datetime))
    end_time = request.args.get("end_time", default=next_hour_timestamp, type=int)

    if end_time <= start_time:
        return jsonify(
            error_message="Specify end timestamp larger than the current hour\"s timestamp."), HTTP_400_BAD_REQUEST

    if city_name is None:
        for city in cache.get("cities") or read_cities():
            for sensor in read_sensors(city["cityName"]):
                fetch_city_data(city["cityName"], sensor)

        return jsonify(success="Fetched weather and pollution data from the external APIs for all cities.")

    if (city := check_city(city_name)) is None:
        return jsonify(
            error_message="Cannot fetch data because the city is not found or is invalid."), HTTP_400_BAD_REQUEST

    if sensor_id is None:
        for sensor in read_sensors(city["cityName"]):
            fetch_city_data(city_name, sensor)

        return jsonify(success="Started the operation to fetch weather and pollution data from the external APIs for "
                               f"{city['siteName']} and all active sensors.")
    else:
        if (sensor := check_sensor(city_name, sensor_id)) is None:
            return jsonify(
                error_message="Data cannot be trained because the sensor is not found or is invalid."), \
                HTTP_404_NOT_FOUND

        fetch_city_data(city_name, sensor)

        return jsonify(success="Started the operation to fetch weather and pollution data from the external APIs for "
                               f"{city['siteName']} and {sensor['description']}.")
