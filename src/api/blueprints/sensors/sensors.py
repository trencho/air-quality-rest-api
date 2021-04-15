from flasgger import swag_from
from flask import Blueprint, jsonify, make_response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from preparation import check_city, check_sensor

sensors_blueprint = Blueprint('sensors', __name__)


@sensors_blueprint.route('/cities/<string:city_name>/sensors/', endpoint='sensors_all', methods=['GET'])
@sensors_blueprint.route('/cities/<string:city_name>/sensors/<string:sensor_id>/', endpoint='sensors_id',
                         methods=['GET'])
@cache.memoize(timeout=3600)
@swag_from('sensors_all.yml', endpoint='sensors.sensors_all', methods=['GET'])
@swag_from('sensors_id.yml', endpoint='sensors.sensors_id', methods=['GET'])
def fetch_city_sensor(city_name, sensor_id=None):
    if check_city(city_name) is None:
        message = 'Cannot return data because the city is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    if sensor_id is None:
        sensors = cache.get('sensors') or {}
        return make_response(jsonify(sensors[city_name]))

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Cannot return data because the sensor is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    return make_response(sensor)
