from flasgger import swag_from
from flask import Blueprint, jsonify, make_response

from api.resources import check_city, check_sensor, fetch_sensors
from definitions import HTTP_NOT_FOUND

sensors = Blueprint('sensor', __name__)


@sensors.route('/cities/<string:city_name>/sensors/', endpoint='sensor_all', methods=['GET'])
@sensors.route('/cities/<string:city_name>/sensors/<string:sensor_id>/', endpoint='sensor_id', methods=['GET'])
@swag_from('sensor_all.yml', endpoint='sensor.sensor_all', methods=['GET'])
@swag_from('sensor_id.yml', endpoint='sensor.sensor_id', methods=['GET'])
def fetch_city_sensor(city_name, sensor_id=None):
    city = check_city(city_name)
    if city is None:
        message = 'Cannot return data because the city is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    if sensor_id is None:
        message = fetch_sensors(city_name)
        return make_response(jsonify(message))

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Cannot return data because the sensor is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    return make_response(jsonify(sensor))
