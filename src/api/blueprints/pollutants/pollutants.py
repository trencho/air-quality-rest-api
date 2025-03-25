from pathlib import Path

from flasgger import swag_from
from flask import Blueprint, jsonify, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.blueprints import fetch_dataframe
from api.config.cache import cache
from definitions import CACHE_TIMEOUTS, POLLUTANTS
from preparation import calculate_nearest_sensor, check_city, check_sensor

pollutants_blueprint = Blueprint("pollutants", __name__)


@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
def fetch_measurements(city_name: str, sensor_id: str) -> Response:
    if isinstance(dataframe := fetch_dataframe(Path(city_name) / sensor_id, "pollution"), Response):
        return dataframe

    measurements = [{"name": POLLUTANTS[pollutant], "value": pollutant}
                    for pollutant in POLLUTANTS if pollutant in dataframe.columns]

    return jsonify(measurements)


@pollutants_blueprint.get("/cities/<string:city_name>/sensors/<string:sensor_id>/pollutants/", endpoint="city_sensor")
@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
@swag_from("pollutants_city_sensor.yml", endpoint="pollutants.city_sensor", methods=["GET"])
def fetch_city_sensor_pollutants(city_name: str, sensor_id: str) -> Response | tuple[Response, int]:
    if check_city(city_name) is None:
        return jsonify(
            error_message="Cannot return available pollutants because the city is not found or is invalid."), \
            HTTP_404_NOT_FOUND

    if check_sensor(city_name, sensor_id) is None:
        return jsonify(
            error_message="Cannot return available pollutants because the sensor is not found or is invalid."), \
            HTTP_404_NOT_FOUND

    return fetch_measurements(city_name, sensor_id)


@pollutants_blueprint.get("/coordinates/<float:latitude>,<float:longitude>/pollutants/", endpoint="coordinates")
@swag_from("pollutants_coordinates.yml", endpoint="pollutants.coordinates", methods=["GET"])
def fetch_coordinates_pollutants(latitude: float, longitude: float) -> Response | tuple[Response, int]:
    if (sensor := calculate_nearest_sensor((latitude, longitude))) is None:
        return jsonify(
            error_message="Cannot return available pollutants because the coordinates are far away from all available "
                          "sensors."), HTTP_404_NOT_FOUND

    return fetch_measurements(sensor["cityName"], sensor["sensorId"])
