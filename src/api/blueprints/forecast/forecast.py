from json import load
from os import path

from flasgger import swag_from
from flask import Blueprint, jsonify, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from api.config.repository import RepositorySingleton
from definitions import DATA_PROCESSED_PATH
from preparation import calculate_nearest_city, calculate_nearest_sensor, check_city, check_sensor, fetch_sensors, \
    location_timezone, read_cities
from processing import current_hour, next_hour

forecast_blueprint = Blueprint("forecast", __name__)
repository = RepositorySingleton.get_instance().get_repository()


@forecast_blueprint.get("/cities/<string:city_name>/forecast/", endpoint="forecast_city")
@cache.memoize(timeout=3600)
@swag_from("forecast_city.yml", endpoint="forecast.forecast_city", methods=["GET"])
def fetch_city_forecast(city_name: str) -> Response | tuple[Response, int]:
    if (city := check_city(city_name)) is None:
        return jsonify(
            error_message="Value cannot be predicted because the city is not found or is invalid."), HTTP_404_NOT_FOUND

    forecast = {"latitude": city["cityLocation"]["latitude"], "longitude": city["cityLocation"]["longitute"]}
    forecast.update(return_city_forecast_results(city))
    return jsonify(forecast)


@forecast_blueprint.get("/cities/coordinates/<float:latitude>,<float:longitude>/forecast/", endpoint="city_coordinates")
@swag_from("forecast_city_sensor_coordinates.yml", endpoint="forecast.city_coordinates", methods=["GET"])
def fetch_city_coordinates_forecast(latitude: float, longitude: float) -> Response | tuple[Response, int]:
    if (city := calculate_nearest_city((latitude, longitude))) is None:
        return jsonify(error_message="Value cannot be predicted because the coordinates are far away from all "
                                     "available cities."), HTTP_404_NOT_FOUND

    forecast = {"latitude": latitude, "longitude": longitude}
    forecast.update(return_city_forecast_results(city))
    return jsonify(forecast)


@forecast_blueprint.get("/cities/<string:city_name>/sensors/<string:sensor_id>/forecast/",
                        endpoint="forecast_city_sensor")
# @cache.memoize(timeout=3600)
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
    forecast = {"latitude": float(sensor_position[0]), "longitude": float(sensor_position[1])}
    forecast.update(return_sensor_forecast_results(city, sensor))
    return jsonify(forecast)


@forecast_blueprint.get("/coordinates/<float:latitude>,<float:longitude>/forecast/", endpoint="sensor_coordinates")
@swag_from("forecast_city_sensor_coordinates.yml", endpoint="forecast.sensor_coordinates", methods=["GET"])
def fetch_city_sensor_coordinates_forecast(latitude: float, longitude: float) -> Response | tuple[Response, int]:
    if (sensor := calculate_nearest_sensor((latitude, longitude))) is None:
        return jsonify(error_message="Value cannot be predicted because the coordinates are far away from all "
                                     "available sensors."), HTTP_404_NOT_FOUND

    for city in cache.get("cities") or read_cities():
        if city["cityName"] == sensor["cityName"]:
            forecast = {"latitude": latitude, "longitude": longitude}
            forecast.update(return_sensor_forecast_results(city, sensor))
            return jsonify(forecast)


def return_city_forecast_results(city: dict) -> dict:
    forecast_results = {"sensors": []}
    sensors = fetch_sensors(city["cityName"])
    for sensor in sensors:
        forecast_results["sensors"].append(return_sensor_forecast_results(city, sensor))
    return forecast_results


def return_sensor_forecast_results(city: dict, sensor: dict) -> dict:
    try:
        with open(path.join(DATA_PROCESSED_PATH, city["cityName"], sensor["sensorId"], "predictions.json"),
                  "r") as in_file:
            data = load(in_file)
            if data[0]["time"] == next_hour(current_hour(tz=location_timezone(city["countryCode"]))):
                return {"data": data}
    except Exception:
        pass

    forecast_result = repository.get(collection_name="predictions",
                                     filter={"cityName": city["cityName"], "sensorId": sensor["sensorId"]})
    if forecast_result is not None and forecast_result["data"]:
        return {"data": forecast_result["data"]}
