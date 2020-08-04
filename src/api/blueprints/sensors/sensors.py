from flasgger import swag_from
from flask import Blueprint, jsonify, make_response

from api.config.cache import cache
from definitions import HTTP_NOT_FOUND
from preparation import check_city, check_sensor

sensors_blueprint = Blueprint('sensors', __name__)


@sensors_blueprint.route('/cities/<string:city_name>/sensors/', endpoint='sensor_all', methods=['GET'])
@sensors_blueprint.route('/cities/<string:city_name>/sensors/<string:sensor_id>/', endpoint='sensor_id',
                         methods=['GET'])
@swag_from('sensor_all.yml', endpoint='sensors.sensor_all', methods=['GET'])
@swag_from('sensor_id.yml', endpoint='sensors.sensor_id', methods=['GET'])
def fetch_city_sensor(city_name, sensor_id=None):
    city = check_city(city_name)
    if city is None:
        message = 'Cannot return data because the city is either missing or invalid.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)

    if sensor_id is None:
        sensors = cache.get('sensors') or {}
        message = sensors[city['cityName']]
        return make_response(jsonify(message))

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Cannot return data because the sensor is either missing or invalid.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)

    return make_response(jsonify(sensor))
