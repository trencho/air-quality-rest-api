from math import modf
from typing import Optional

from haversine import haversine_vector
from numpy import where
from requests import get as requests_get

from api.config.cache import cache
from definitions import countries


@cache.memoize(timeout=3600)
def check_city(city_name: str) -> Optional[dict]:
    cities = cache.get('cities') or []
    for city in cities:
        if city['cityName'] == city_name:
            return city

    return None


@cache.memoize(timeout=3600)
def check_sensor(city_name: str, sensor_id: str) -> Optional[dict]:
    sensors = cache.get('sensors') or {}
    for sensor in sensors[city_name]:
        if sensor['sensorId'] == sensor_id:
            return sensor

    return None


def fetch_cities() -> list:
    response = requests_get('https://pulse.eco/rest/city/')
    try:
        cities_json = response.json()
        return [city for city in cities_json if city['countryCode'] in countries]
    except ValueError:
        return []


def fetch_sensors(city_name: str) -> list:
    response = requests_get(f'https://{city_name}.pulse.eco/rest/sensor/')
    try:
        sensors_json = response.json()
        return [sensor for sensor in sensors_json if sensor['status'] == 'ACTIVE']
    except ValueError:
        return []


def recalculate_coordinate(val: tuple, _as: Optional[str] = None) -> [float, tuple]:
    """
    Accepts a coordinate as a tuple (degree, minutes, seconds) You can give only one of them (e.g. only minutes as a
    floating point number) and it will be duly recalculated into degrees, minutes and seconds. Return value can be
    specified as 'deg', 'min' or 'sec'; default return value is a proper coordinate tuple.
    """
    degrees, minutes, seconds = val
    # Pass outstanding values from right to left
    minutes = (minutes or 0) + int(seconds) / 60
    seconds = seconds % 60
    degrees = (degrees or 0) + int(minutes) / 60
    minutes = minutes % 60
    # Pass decimal part from left to right
    degrees_fraction, degrees_integer = modf(degrees)
    minutes = minutes + degrees_fraction * 60
    degrees = degrees_integer
    minutes_fraction, minutes_integer = modf(minutes)
    seconds = seconds + minutes_fraction * 60
    minutes = minutes_integer
    if _as:
        seconds = seconds + minutes * 60 + degrees * 3600
        if _as == 'sec':
            return seconds
        if _as == 'min':
            return seconds / 60
        if _as == 'deg':
            return seconds / 3600
    return degrees, minutes, seconds


def calculate_nearest_sensor(coordinates: tuple, radius_of_effect: int = 2) -> Optional[dict]:
    sensors = [sensor for sensor_list in list(cache.get('sensors').values()) for sensor in sensor_list]
    distances = haversine_vector(coordinates, [tuple(map(float, sensor['position'].split(','))) for sensor in sensors],
                                 comb=True)
    min_distance = min(distances)
    return sensors[where(distances == min_distance)[0][0]] if min_distance <= radius_of_effect else None
