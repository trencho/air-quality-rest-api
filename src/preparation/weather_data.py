from os import environ, path
from time import sleep
from traceback import print_exc

from pandas import DataFrame, json_normalize
from requests import get as requests_get

from definitions import DATA_RAW_PATH, open_weather_token
from processing import flatten_json
from .handle_data import save_dataframe


def fetch_weather_data(city_name, sensor):
    url = 'https://api.openweathermap.org/data/2.5/onecall'
    sensor_position = sensor['position'].split(',')
    lat, lon = float(sensor_position[0]), float(sensor_position[1])
    units = 'metric'
    exclude = 'alerts,current,daily,minutely'
    token = environ[open_weather_token]
    params = f'lat={lat}&lon={lon}&units={units}&exclude={exclude}&appid={token}'

    dataframe = DataFrame()
    weather_response = requests_get(url=url, params=params)
    try:
        weather_json = weather_response.json()
        hourly_data = weather_json['hourly']
        df = json_normalize([flatten_json(hourly) for hourly in hourly_data])
        df.rename(columns={'dt': 'time'}, inplace=True, errors='ignore')
        dataframe = dataframe.append(df, ignore_index=True)
        dataframe.drop(columns='weather', inplace=True, errors='ignore')
        sleep(1)
    except Exception:
        print(weather_response)
        print_exc()
        return

    if not dataframe.empty:
        data_path = path.join(DATA_RAW_PATH, city_name, sensor['sensorId'], 'weather.csv')
        save_dataframe(dataframe, 'weather', data_path, sensor['sensorId'])
