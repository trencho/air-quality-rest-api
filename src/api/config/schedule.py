from datetime import datetime

from api.resources import fetch_cities, fetch_city_data, fetch_sensors, next_hour, train_city_sensors
from api.resources.fetch import current_hour
from definitions import pollutants


def schedule_fetch_date():
    current_datetime = current_hour(datetime.now())
    current_timestamp = int(datetime.timestamp(current_datetime))
    start_time = current_timestamp

    next_hour_datetime = next_hour(current_datetime)
    next_hour_timestamp = int(datetime.timestamp(next_hour_datetime))
    end_time = next_hour_timestamp

    cities = fetch_cities()
    for city in cities:
        sensors = fetch_sensors(city['cityName'])
        for sensor in sensors:
            fetch_city_data(city['cityName'], sensor, start_time, end_time)


def schedule_model_training():
    cities = fetch_cities()
    for city in cities:
        sensors = fetch_sensors(city['cityName'])
        for sensor in sensors:
            for pollutant in pollutants:
                train_city_sensors(city, sensor, pollutant)
