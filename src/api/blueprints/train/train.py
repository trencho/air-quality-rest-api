from typing import Optional

from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, request, Response
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from definitions import pollutants
from modeling import train_city_sensors
from preparation import check_city, check_sensor

train_blueprint = Blueprint('train', __name__)


@train_blueprint.route('/train/', endpoint='train_all', methods=['GET'])
@train_blueprint.route('/cities/<string:city_name>/train/', endpoint='train_city', methods=['GET'])
@train_blueprint.route('/cities/<string:city_name>/sensors/<string:sensor_id>/train/', endpoint='train_city_sensor',
                       methods=['GET'])
@swag_from('train_all.yml', endpoint='train.train_all', methods=['GET'])
@swag_from('train_city.yml', endpoint='train.train_city', methods=['GET'])
@swag_from('train_city_sensor.yml', endpoint='train.train_city_sensor', methods=['GET'])
def train_data(city_name: str = None, sensor_id: str = None) -> Response:
    pollutant_name = request.args.get('pollutant', default=None, type=Optional[str])
    if pollutant_name is not None and pollutant_name not in pollutants:
        message = 'Data cannot be trained because the pollutant is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    if city_name is None:
        sensors = cache.get('sensors') or {}
        for city in cache.get('cities') or []:
            for sensor in sensors[city['cityName']]:
                if pollutant_name is None:
                    for pollutant in pollutants:
                        train_city_sensors(city, sensor, pollutant)
                else:
                    train_city_sensors(city, sensor, pollutant_name)

    if (city := check_city(city_name)) is None:
        message = 'Data cannot be trained because the city is not found or is invalid.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

    if sensor_id is None:
        sensors = cache.get('sensors') or {}
        for sensor in sensors[city['cityName']]:
            if pollutant_name is None:
                for pollutant in pollutants:
                    train_city_sensors(city, sensor, pollutant)
            else:
                train_city_sensors(city, sensor, pollutant_name)
    else:
        if (sensor := check_sensor(city_name, sensor_id)) is None:
            message = 'Data cannot be trained because the sensor is not found or is invalid.'
            return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)

        if pollutant_name is None:
            for pollutant in pollutants:
                train_city_sensors(city, sensor, pollutant)
        else:
            train_city_sensors(city, sensor, pollutant_name)

    message = 'Training initialized...'
    return make_response(jsonify(success=message))
