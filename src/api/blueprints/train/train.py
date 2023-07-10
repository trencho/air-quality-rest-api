from typing import Optional

from flasgger import swag_from
from flask import Blueprint, jsonify, request, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from definitions import POLLUTANTS
from modeling import train_city_sensors
from preparation import check_city, check_sensor, read_cities, read_sensors

train_blueprint = Blueprint("train", __name__)


@train_blueprint.get("/train/", endpoint="train_all")
@train_blueprint.get("/cities/<string:city_name>/train/", endpoint="train_city")
@train_blueprint.get("/cities/<string:city_name>/sensors/<string:sensor_id>/train/", endpoint="train_city_sensor")
@swag_from("train_all.yml", endpoint="train.train_all", methods=["GET"])
@swag_from("train_city.yml", endpoint="train.train_city", methods=["GET"])
@swag_from("train_city_sensor.yml", endpoint="train.train_city_sensor", methods=["GET"])
def train_data(city_name: str = None, sensor_id: str = None) -> Response | tuple[Response, int]:
    pollutant_name = request.args.get("pollutant", default=None, type=Optional[str])
    if pollutant_name is not None and pollutant_name not in POLLUTANTS:
        return jsonify(
            error_message="Data cannot be trained because the pollutant is not found or is invalid."), \
            HTTP_404_NOT_FOUND

    if city_name is None:
        for city in cache.get("cities") or read_cities():
            for sensor in read_sensors(city["cityName"]):
                if pollutant_name is None:
                    for pollutant in POLLUTANTS:
                        train_city_sensors(city, sensor, pollutant)
                else:
                    train_city_sensors(city, sensor, pollutant_name)

    if (city := check_city(city_name)) is None:
        return jsonify(
            error_message="Data cannot be trained because the city is not found or is invalid."), HTTP_404_NOT_FOUND

    if sensor_id is None:
        for sensor in read_sensors(city["cityName"]):
            if pollutant_name is None:
                for pollutant in POLLUTANTS:
                    train_city_sensors(city, sensor, pollutant)
            else:
                train_city_sensors(city, sensor, pollutant_name)
    else:
        if (sensor := check_sensor(city_name, sensor_id)) is None:
            return jsonify(
                error_message="Data cannot be trained because the sensor is not found or is invalid."), \
                HTTP_404_NOT_FOUND

        if pollutant_name is None:
            for pollutant in POLLUTANTS:
                train_city_sensors(city, sensor, pollutant)
        else:
            train_city_sensors(city, sensor, pollutant_name)

    return jsonify(success="Training initialized...")
