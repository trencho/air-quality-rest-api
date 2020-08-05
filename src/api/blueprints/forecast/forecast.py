from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response, request

from api.blueprints import forecast_city_sensor, next_hour
from api.config.cache import cache
from definitions import HTTP_BAD_REQUEST, HTTP_NOT_FOUND, pollutants
from preparation import check_city, check_sensor

forecast_blueprint = Blueprint('forecast', __name__)


@forecast_blueprint.route('/pollutants/<string:pollutant_name>/forecast', endpoint='forecast_all', methods=['GET'])
@forecast_blueprint.route('/pollutants/<string:pollutant_name>/cities/<string:city_name>/forecast',
                          endpoint='forecast_city', methods=['GET'])
@forecast_blueprint.route(
    '/pollutants/<string:pollutant_name>/cities/<string:city_name>/sensors/<string:sensor_id>/forecast',
    endpoint='forecast_city_sensor', methods=['GET'])
@swag_from('forecast_all.yml', endpoint='forecast.forecast_all', methods=['GET'])
@swag_from('forecast_city.yml', endpoint='forecast.forecast_city', methods=['GET'])
@swag_from('forecast_city_sensor.yml', endpoint='forecast.forecast_city_sensor', methods=['GET'])
@cache.memoize(timeout=3600)
def fetch_forecast(pollutant_name, city_name=None, sensor_id=None):
    if pollutant_name not in pollutants:
        message = 'Value cannot be predicted because the pollutant is either missing or invalid.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)

    next_hour_time = next_hour(datetime.now())
    next_hour_timestamp = int(datetime.timestamp(next_hour_time))
    timestamp = request.args.get('timestamp', default=next_hour_timestamp, type=int)
    if timestamp < next_hour_timestamp:
        message = ('Cannot forecast pollutant because the timestamp is in the past. '
                   'Send a GET request to the history endpoint for past values.')
        return make_response(jsonify(error_message=message), HTTP_BAD_REQUEST)

    forecast_results = []
    if city_name is None:
        cities = cache.get('cities') or []
        sensors = cache.get('sensors') or {}
        for city in cities:
            for sensor in sensors[city['cityName']]:
                forecast_result = forecast_city_sensor(city, sensor, pollutant_name, timestamp)
                if isinstance(forecast_result, Response):
                    return forecast_result

                forecast_results.append(forecast_result)

        return make_response(jsonify(forecast_results))

    city = check_city(city_name)
    if city is None:
        message = 'Value cannot be predicted because the city is either missing or invalid.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)

    if sensor_id is None:
        sensors = cache.get('sensors') or {}
        for sensor in sensors[city['cityName']]:
            forecast_result = forecast_city_sensor(city, sensor, pollutant_name, timestamp)
            if isinstance(forecast_result, Response):
                return forecast_result

            forecast_results.append(forecast_result)

        return make_response(jsonify(forecast_results))

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Value cannot be predicted because the sensor is either missing or inactive.'
        return make_response(jsonify(error_message=message), HTTP_NOT_FOUND)

    forecast_result = forecast_city_sensor(city, sensor, pollutant_name, timestamp)
    if isinstance(forecast_result, Response):
        return forecast_result

    forecast_results.append(forecast_result)
    return make_response(jsonify(forecast_results))
