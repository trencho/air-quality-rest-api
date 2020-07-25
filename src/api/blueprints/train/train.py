from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, request

from api.blueprints import train_city_sensors
from definitions import HTTP_NOT_FOUND, pollutants
from preparation import check_city, check_sensor
from preparation.location_data import cities, sensors

train_blueprint = Blueprint('train', __name__)


@train_blueprint.route('/train/', endpoint='train_all', methods=['GET'])
@train_blueprint.route('/cities/<string:city_name>/train/', endpoint='train_city', methods=['GET'])
@train_blueprint.route('/cities/<string:city_name>/sensors/<string:sensor_id>/train/', endpoint='train_city_sensor',
                       methods=['GET'])
@swag_from('train_all.yml', endpoint='train.train_all', methods=['GET'])
@swag_from('train_city.yml', endpoint='train.train_city', methods=['GET'])
@swag_from('train_city_sensor.yml', endpoint='train.train_city_sensor', methods=['GET'])
def train_data(city_name=None, sensor_id=None):
    pollutant_name = request.args.get('pollutant', default=None, type=str)
    if pollutant_name is not None and pollutant_name not in pollutants:
        message = 'Data cannot be trained because the pollutant is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    if city_name is None:
        for city in cities:
            for sensor in sensors[city['cityName']]:
                if pollutant_name is None:
                    for pollutant in pollutants:
                        train_city_sensors(city, sensor, pollutant)
                else:
                    train_city_sensors(city, sensor, pollutant_name)

    city = check_city(city_name)
    if city is None:
        message = 'Data cannot be trained because the city is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    if sensor_id is None:
        for sensor in sensors[city['cityName']]:
            if pollutant_name is None:
                for pollutant in pollutants:
                    train_city_sensors(city, sensor, pollutant)
            else:
                train_city_sensors(city, sensor, pollutant_name)
    else:
        sensor = check_sensor(city_name, sensor_id)
        if sensor is None:
            message = 'Data cannot be trained because the sensor is either missing or invalid.'
            status_code = HTTP_NOT_FOUND
            return make_response(jsonify(error_message=message), status_code)

        if pollutant_name is None:
            for pollutant in pollutants:
                train_city_sensors(city, sensor, pollutant)
        else:
            train_city_sensors(city, sensor, pollutant_name)

    message = 'Training initialized...'
    return make_response(jsonify(success=message))
