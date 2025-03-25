from json import loads

from flasgger import swag_from
from flask import Blueprint, jsonify, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from api.config.repository import RepositorySingleton
from definitions import CACHE_TIMEOUTS, DATA_PROCESSED_PATH
from preparation import calculate_nearest_city, calculate_nearest_sensor, check_city, check_sensor, location_timezone, \
    read_sensors
from processing import current_hour, next_hour

forecast_blueprint = Blueprint("forecast", __name__)
repository = RepositorySingleton.get_instance().get_repository()


@forecast_blueprint.get("/cities/<string:city_name>/forecast/", endpoint="forecast_city")
@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
@swag_from("forecast_city.yml", endpoint="forecast.forecast_city", methods=["GET"])
def fetch_city_forecast(city_name: str) -> Response | tuple[Response, int]:
    if (city := check_city(city_name)) is None:
        return jsonify(
            error_message="Value cannot be predicted because the city is not found or is invalid."), HTTP_404_NOT_FOUND

    return jsonify(return_city_forecast_results(city))


@forecast_blueprint.get("/cities/coordinates/<float:latitude>,<float:longitude>/forecast/", endpoint="city_coordinates")
@swag_from("forecast_city_coordinates.yml", endpoint="forecast.city_coordinates", methods=["GET"])
def fetch_city_coordinates_forecast(latitude: float, longitude: float) -> Response | tuple[Response, int]:
    if (city := calculate_nearest_city((latitude, longitude))) is None:
        return jsonify(error_message="Value cannot be predicted because the coordinates are far away from all "
                                     "available cities."), HTTP_404_NOT_FOUND

    forecast = return_city_forecast_results(city)
    forecast.update({"latitude": latitude, "longitude": longitude})
    return jsonify(forecast)


@forecast_blueprint.get("/cities/<string:city_name>/sensors/<string:sensor_id>/forecast/",
                        endpoint="forecast_city_sensor")
@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
@swag_from("forecast_sensor.yml", endpoint="forecast.forecast_city_sensor", methods=["GET"])
def fetch_sensor_forecast(city_name: str, sensor_id: str) -> Response | tuple[Response, int]:
    if (city := check_city(city_name)) is None:
        return jsonify(
            error_message="Value cannot be predicted because the city is not found or is invalid."), HTTP_404_NOT_FOUND

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        return jsonify(
            error_message="Value cannot be predicted because the sensor is not found or inactive."), HTTP_404_NOT_FOUND

    return jsonify(return_sensor_forecast_results(city, sensor))


@forecast_blueprint.get("/sensors/coordinates/<float:latitude>,<float:longitude>/forecast/",
                        endpoint="sensor_coordinates")
@swag_from("forecast_sensor_coordinates.yml", endpoint="forecast.sensor_coordinates", methods=["GET"])
def fetch_sensor_coordinates_forecast(latitude: float, longitude: float) -> Response | tuple[Response, int]:
    if (sensor := calculate_nearest_sensor((latitude, longitude))) is None:
        return jsonify(error_message="Value cannot be predicted because the coordinates are far away from all "
                                     "available sensors."), HTTP_404_NOT_FOUND

    if (city := check_city(sensor["cityName"])) is not None:
        forecast = return_sensor_forecast_results(city, sensor)
        forecast.update({"latitude": latitude, "longitude": longitude})
        return jsonify(forecast)

    return jsonify(
        error_message="Value cannot be predicted because the sensor is not found or is invalid."), HTTP_404_NOT_FOUND


def return_city_forecast_results(city: dict) -> dict:
    forecast_results = {"latitude": city["cityLocation"]["latitude"], "longitude": city["cityLocation"]["longitute"],
                        "sensors": []}
    sensors = read_sensors(city["cityName"])
    for sensor in sensors:
        forecast_results["sensors"].append(return_sensor_forecast_results(city, sensor))
    return forecast_results


def return_sensor_forecast_results(city: dict, sensor: dict) -> dict:
    sensor_position = sensor["position"].split(",")
    forecast = {"latitude": float(sensor_position[0]), "longitude": float(sensor_position[1])}
    try:
        data = loads((DATA_PROCESSED_PATH / city["cityName"] / sensor["sensorId"] / "predictions.json").read_text())
        if data[0]["time"] == next_hour(current_hour(tz=location_timezone(city["countryCode"]))):
            forecast.update({"data": data})
            return forecast
    except Exception:
        pass

    forecast_result = repository.get(collection_name="predictions",
                                     filter={"cityName": city["cityName"], "sensorId": sensor["sensorId"]})
    if forecast_result is not None:
        forecast.update({"data": forecast_result["data"]})
        return forecast

    forecast.update({"data": []})
    return forecast
