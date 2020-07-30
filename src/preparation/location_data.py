from requests import get as requests_get

from api.config.cache import cache
from api.config.database import mongo


def check_city(city_name):
    cities = cache.get('cities') or []
    for city in cities:
        if city['cityName'] == city_name:
            return city

    return None


def check_sensor(city_name, sensor_id):
    sensors = cache.get('sensors') or {}
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


def fetch_locations():
    cities = list(mongo.db['cities'].find(projection={'_id': False}))
    cache.set('cities', cities)
    sensors = {}
    for city in cities:
        sensors[city['cityName']] = list(mongo.db['sensors'].find({'cityName': city['cityName']},
                                                                  projection={'_id': False}))
    cache.set('sensors', sensors)


def fetch_sensors(city_name):
    response = requests_get(f'https://{city_name}.pulse.eco/rest/sensor/')
    try:
        sensors_json = response.json()
        return [sensor for sensor in sensors_json if sensor['status'] == 'ACTIVE']
    except ValueError:
        return []
