from datetime import datetime
from json import loads
from os import path

from flasgger import swag_from
from flask import Blueprint, jsonify, Response, request
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from api.blueprints import fetch_dataframe
from api.config.cache import cache
from preparation import calculate_nearest_sensor, check_city, check_sensor
from processing import current_hour

history_blueprint = Blueprint("history", __name__)

data_types = ["pollution", "weather"]


@history_blueprint.get("/cities/<string:city_name>/sensors/<string:sensor_id>/history/<string:data_type>/",
                       endpoint="city_sensor")
@swag_from("history_city_sensor.yml", endpoint="history.city_sensor", methods=["GET"])
def fetch_city_sensor_history(city_name: str, sensor_id: str, data_type: str) -> Response | tuple[Response, int]:
    if data_type not in data_types:
        return jsonify(
            error_message="Cannot return historical data because the data type is not found or is invalid."), \
            HTTP_404_NOT_FOUND

    if isinstance(timestamps := retrieve_history_timestamps(), Response):
        return timestamps
    start_time, end_time = timestamps

    if check_city(city_name) is None:
        return jsonify(
            error_message="Cannot return historical data because the city is not found or is invalid."), \
            HTTP_404_NOT_FOUND

    if (sensor := check_sensor(city_name, sensor_id)) is None:
        return jsonify(
            error_message="Cannot return historical data because the sensor is not found or is invalid."), \
            HTTP_404_NOT_FOUND

    return return_historical_data(city_name, sensor, data_type, start_time, end_time)


@history_blueprint.get("/coordinates/<float:latitude>,<float:longitude>/history/<string:data_type>/",
                       endpoint="coordinates")
@swag_from("history_coordinates.yml", endpoint="history.coordinates", methods=["GET"])
def fetch_coordinates_history(latitude: float, longitude: float, data_type: str) -> Response | tuple[Response, int]:
    if data_type not in data_types:
        return jsonify(
            error_message="Cannot return historical data because the data type is not found or is invalid."), \
            HTTP_404_NOT_FOUND

    if isinstance(timestamps := retrieve_history_timestamps(), Response):
        return timestamps
    start_time, end_time = timestamps

    if (sensor := calculate_nearest_sensor((latitude, longitude))) is None:
        return jsonify(
            error_message="Cannot return historical data because the coordinates are far away from all available "
                          "sensors."), HTTP_404_NOT_FOUND

    return return_historical_data(sensor["cityName"], sensor, data_type, start_time, end_time)


def retrieve_history_timestamps() -> tuple[int, int] | tuple[Response, int]:
    current_datetime = current_hour()
    current_timestamp = int(datetime.timestamp(current_datetime))
    week_in_seconds = 604800
    start_time = request.args.get("start_time", default=current_timestamp - week_in_seconds, type=int)
    end_time = request.args.get("end_time", default=current_timestamp, type=int)
    if start_time > end_time:
        return jsonify(
            error_message="Specify end timestamp larger than the current hour\"s timestamp."), HTTP_400_BAD_REQUEST
    if end_time > start_time + week_in_seconds:
        return jsonify(error_message="Specify start and end time in one week range."), HTTP_400_BAD_REQUEST

    return start_time, end_time


@cache.memoize(timeout=3600)
def return_historical_data(city_name: str, sensor: dict, data_type: str, start_time: int, end_time: int) -> Response:
    if isinstance(dataframe := fetch_dataframe(path.join(city_name, sensor["sensorId"]), data_type), Response):
        return dataframe

    dataframe = dataframe.loc[(dataframe["time"] >= start_time) & (dataframe["time"] <= end_time)]
    sensor_position = sensor["position"].split(",")
    latitude, longitude = float(sensor_position[0]), float(sensor_position[1])
    history_results = {"latitude": latitude, "longitude": longitude,
                       "data": list(loads(dataframe.to_json(orient="records")))}
    return jsonify(history_results)
