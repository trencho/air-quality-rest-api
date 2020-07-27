from requests import get as requests_get

from api.config.db import mongo
from definitions import status_active

cities = []
sensors = {}


def check_city(city_name):
    for city in cities:
        if city['cityName'] == city_name:
            return city

    return None


def check_sensor(city_name, sensor_id):
    for sensor in sensors[city_name]:
        if sensor['sensorId'] == sensor_id:
            return sensor

    return None


def fetch_cities():
    response = requests_get('https://pulse.eco/rest/city/')
    try:
        return response.json()
    except ValueError:
        return []


def fetch_sensors(city_name):
    response = requests_get(f'https://{city_name}.pulse.eco/rest/sensor/')
    try:
        sensors_json = response.json()
        return [sensor for sensor in sensors_json if sensor['status'] == status_active]
    except ValueError:
        return []


def fetch_locations():
    cities = list(mongo.db['cities'].find())
    for city in cities:
        sensors.update({city['cityName']: mongo.db['sensors'].find({'cityName': city['cityName']})})
