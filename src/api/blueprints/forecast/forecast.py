from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, jsonify, make_response, Response, request

from api.blueprints import forecast_city_sensor, next_hour
from definitions import HTTP_BAD_REQUEST, HTTP_NOT_FOUND, pollutants
from preparation import check_city, check_sensor, fetch_cities, fetch_sensors

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
def forecast_pollutant(pollutant_name, city_name=None, sensor_id=None):
    if pollutant_name not in pollutants:
        message = 'Value cannot be predicted because the pollutant is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    next_hour_time = next_hour(datetime.now())
    next_hour_timestamp = int(datetime.timestamp(next_hour_time))
    timestamp = request.args.get('timestamp', default=next_hour_timestamp, type=int)
    if timestamp < next_hour_timestamp:
        message = ('Cannot forecast pollutant because the timestamp is in the past. '
                   'Send a GET request to the history endpoint for past values.')
        status_code = HTTP_BAD_REQUEST
        return make_response(jsonify(error_message=message), status_code)

    forecast_results = []
    if city_name is None:
        cities = fetch_cities()
        for city in cities:
            sensors = fetch_sensors(city['cityName'])
            for sensor in sensors:
                forecast_result = forecast_city_sensor(city, sensor, pollutant_name, timestamp)
                if isinstance(forecast_result, Response):
                    return forecast_result

                forecast_results.append(forecast_result)

        return make_response(jsonify(forecast_results))

    city = check_city(city_name)
    if city is None:
        message = 'Value cannot be predicted because the city is either missing or invalid.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    if sensor_id is None:
        sensors = fetch_sensors(city['cityName'])
        for sensor in sensors:
            forecast_result = forecast_city_sensor(city, sensor, pollutant_name, timestamp)
            if isinstance(forecast_result, Response):
                return forecast_result

            forecast_results.append(forecast_result)

        return make_response(jsonify(forecast_results))

    sensor = check_sensor(city_name, sensor_id)
    if sensor is None:
        message = 'Value cannot be predicted because the sensor is either missing or inactive.'
        status_code = HTTP_NOT_FOUND
        return make_response(jsonify(error_message=message), status_code)

    forecast_result = forecast_city_sensor(city, sensor, pollutant_name, timestamp)
    if isinstance(forecast_result, Response):
        return forecast_result

    forecast_results.append(forecast_result)
    return make_response(jsonify(forecast_results))
