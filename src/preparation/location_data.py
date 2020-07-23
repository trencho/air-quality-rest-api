from requests import get as requests_get

from definitions import status_active

cities = None
sensors = None


def check_city(city_name):
    cities = fetch_cities()
    for city in cities:
        if city['cityName'] == city_name:
            return city

    return None


def check_sensor(city_name, sensor_id):
    sensors = fetch_sensors(city_name)
    for sensor in sensors:
        if sensor['sensorId'] == sensor_id:
            return sensor

    return None


def fetch_cities():
    url = 'https://pulse.eco/rest/city/'
    response = requests_get(url)
    try:
        cities_json = response.json()
    except ValueError:
        return []

    return cities_json


def fetch_sensors(city_name):
    url = f'https://{city_name}.pulse.eco/rest/sensor/'
    response = requests_get(url)
    try:
        sensors_json = response.json()
    except ValueError:
        return []

    active_sensors = [sensor for sensor in sensors_json if sensor['status'] == status_active]

    return active_sensors


def fetch_locations():
    pass
