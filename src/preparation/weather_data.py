from os import environ, path
from time import sleep

from pandas import json_normalize
from requests import get

from api.config.logger import log
from definitions import DATA_RAW_PATH, open_weather_token
from processing import flatten_json
from .handle_data import save_dataframe


def fetch_weather_data(city_name: str, sensor: dict) -> None:
    url = 'https://api.openweathermap.org/data/2.5/onecall'
    sensor_position = sensor['position'].split(',')
    lat, lon = float(sensor_position[0]), float(sensor_position[1])
    units = 'metric'
    exclude = 'alerts,current,daily,minutely'
    token = environ[open_weather_token]
    params = f'lat={lat}&lon={lon}&units={units}&exclude={exclude}&appid={token}'

    try:
        weather_response = get(url, params)
        hourly_data = weather_response.json()['hourly']
        dataframe = json_normalize([flatten_json(hourly) for hourly in hourly_data])
        dataframe.rename(columns={'dt': 'time'}, inplace=True, errors='ignore')
        dataframe.drop(columns='weather', inplace=True, errors='ignore')

        if len(dataframe.index) > 0:
            save_dataframe(dataframe, 'weather', path.join(DATA_RAW_PATH, city_name, sensor['sensorId'], 'weather.csv'),
                           sensor['sensorId'])
    except Exception:
        log.error(f'Error occurred while fetching weather data for {city_name} - {sensor["sensorId"]}', exc_info=1)
    finally:
        sleep(1)
