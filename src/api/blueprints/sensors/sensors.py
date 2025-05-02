from flasgger import swag_from
from flask import Blueprint, jsonify, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from definitions import CACHE_TIMEOUTS
from preparation import check_city, check_sensor, read_sensors

sensors_blueprint = Blueprint("sensors", __name__)


@sensors_blueprint.get("/cities/<string:city_name>/sensors/", endpoint="sensors_all")
@sensors_blueprint.get(
    "/cities/<string:city_name>/sensors/<string:sensor_id>/", endpoint="sensors_id"
)
@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
@swag_from("sensors_all.yml", endpoint="sensors.sensors_all", methods=["GET"])
@swag_from("sensors_id.yml", endpoint="sensors.sensors_id", methods=["GET"])
def fetch_city_sensor(
    city_name: str, sensor_id: str = None
) -> Response | tuple[Response, int]:
    if check_city(city_name) is None:
        return (
            jsonify(
                error_message="Cannot return data because the city is not found or is invalid."
            ),
            HTTP_404_NOT_FOUND,
        )

    if sensor_id is None:
        return jsonify(read_sensors(city_name))

    if (sensor := check_sensor(city_name, sensor_id)) is None:
        return (
            jsonify(
                error_message="Cannot return data because the sensor is not found or is invalid."
            ),
            HTTP_404_NOT_FOUND,
        )

    return jsonify(sensor)
