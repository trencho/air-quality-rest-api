from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.blueprints import fetch_dataframe
from api.config.cache import cache
from definitions import POLLUTANTS
from preparation import calculate_nearest_sensor, check_city, check_sensor

pollutants_blueprint = Blueprint("pollutants", __name__)


@cache.memoize(timeout=3600)
def fetch_measurements(city_name: str, sensor_id: str) -> Response:
    if isinstance(dataframe := fetch_dataframe(city_name, sensor_id, "pollution"), Response):
        return dataframe

    measurements = [{"name": POLLUTANTS[pollutant], "value": pollutant}
                    for pollutant in POLLUTANTS if pollutant in dataframe.columns]

    return make_response(jsonify(measurements))


@pollutants_blueprint.get("/cities/<string:city_name>/sensors/<string:sensor_id>/pollutants/", endpoint="city_sensor")
@cache.memoize(timeout=3600)
@swag_from("pollutants_city_sensor.yml", endpoint="pollutants.city_sensor", methods=["GET"])
def fetch_city_sensor_pollutants(city_name: str, sensor_id: str) -> Response:
    if check_city(city_name) is None:
        message = "Cannot return available pollutants because the city is not found or is invalid."
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    if (sensor := check_sensor(city_name, sensor_id)) is None:
        message = "Cannot return available pollutants because the sensor is not found or is invalid."
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    return fetch_measurements(sensor["cityName"], sensor["sensorId"])


@pollutants_blueprint.get("/coordinates/<float:latitude>,<float:longitude>/pollutants/", endpoint="coordinates")
@swag_from("pollutants_coordinates.yml", endpoint="pollutants.coordinates", methods=["GET"])
def fetch_coordinates_pollutants(latitude: float, longitude: float) -> Response:
    if (sensor := calculate_nearest_sensor((latitude, longitude))) is None:
        message = "Cannot return available pollutants because the coordinates are far away from all available sensors."
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    return fetch_measurements(sensor["cityName"], sensor["sensorId"])
