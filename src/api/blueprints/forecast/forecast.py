from json import load
from os import path

from flasgger import swag_from
from flask import Blueprint, jsonify, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from api.config.repository import RepositorySingleton
from definitions import DATA_PROCESSED_PATH
from preparation import calculate_nearest_sensor, check_city, check_sensor, location_timezone, read_cities
from processing import current_hour, next_hour

forecast_blueprint = Blueprint("forecast", __name__)
repository = RepositorySingleton.get_instance().get_repository()


@forecast_blueprint.get("/cities/<string:city_name>/sensors/<string:sensor_id>/forecast/",
                        endpoint="forecast_city_sensor")
@cache.memoize(timeout=3600)
@swag_from("forecast_city_sensor.yml", endpoint="forecast.forecast_city_sensor", methods=["GET"])
def fetch_city_sensor_forecast(city_name: str, sensor_id: str) -> Response | tuple[Response, int]:
    if (city := check_city(city_name)) is None:
        return jsonify(
            error_message="Value cannot be predicted because the city is not found or is invalid."), HTTP_404_NOT_FOUND

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        return jsonify(
            error_message="Value cannot be predicted because the sensor is not found or inactive."), HTTP_404_NOT_FOUND

    sensor_position = sensor["position"].split(",")
    latitude, longitude = float(sensor_position[0]), float(sensor_position[1])
    return return_forecast_results(latitude, longitude, city, sensor)


@forecast_blueprint.get("/coordinates/<float:latitude>,<float:longitude>/forecast/", endpoint="coordinates")
@swag_from("forecast_coordinates.yml", endpoint="forecast.coordinates", methods=["GET"])
def fetch_coordinates_forecast(latitude: float, longitude: float) -> Response | tuple[Response, int]:
    if (sensor := calculate_nearest_sensor((latitude, longitude))) is None:
        return jsonify(error_message="Value cannot be predicted because the coordinates are far away from all "
                                     "available sensors."), HTTP_404_NOT_FOUND

    for city in cache.get("cities") or read_cities():
        if city["cityName"] == sensor["cityName"]:
            return return_forecast_results(latitude, longitude, city, sensor)


def return_forecast_results(latitude: float, longitude: float, city: dict, sensor: dict) -> Response:
    forecast_results = {"latitude": latitude, "longitude": longitude, "data": []}
    try:
        with open(path.join(DATA_PROCESSED_PATH, city["cityName"], sensor["sensorId"], "predictions.json"),
                  "r") as in_file:
            data = load(in_file)
            if data[0]["time"] == next_hour(current_hour(tz=location_timezone(city["countryCode"]))):
                forecast_results["data"] = data
                return jsonify(forecast_results)
    except Exception:
        pass

    forecast_result = repository.get(collection_name="predictions",
                                     filter={"cityName": city["cityName"], "sensorId": sensor["sensorId"]})
    if forecast_result is not None and forecast_result["data"]:
        forecast_results["data"] = forecast_result["data"]

    return jsonify(forecast_results)
