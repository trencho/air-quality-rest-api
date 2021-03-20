from os import environ, path
from traceback import format_exc

from pandas import DataFrame, json_normalize
from requests import get as requests_get

from definitions import DATA_EXTERNAL_PATH, open_weather_token
from processing import flatten_json
from .handle_data import save_dataframe

day_in_seconds = 86400


def fetch_weather_data(city_name, sensor, start_time, end_time):
    url = 'https://api.openweathermap.org/data/2.5/onecall'
    sensor_position = sensor['position'].split(',')
    lat, lon = float(sensor_position[0]), float(sensor_position[1])
    units = 'metric'
    exclude = 'current,minutely,daily'
    token = environ[open_weather_token]
    params = f'lat={lat}&lon={lon}&units={units}&exclude={exclude}&appid={token}'

    dataframe = DataFrame()
    while start_time < end_time:
        weather_response = requests_get(url=url, params=params)
        try:
            weather_json = weather_response.json()
            hourly_data = weather_json['hourly']
            df = json_normalize([flatten_json(hourly) for hourly in hourly_data])
            df.rename(columns={'dt': 'time'}, inplace=True, errors='ignore')
            dataframe = dataframe.append(df, ignore_index=True)
        except (KeyError, ValueError):
            print(weather_response)
            print(format_exc())

    dataframe.sort_values(by='time', inplace=True)
    dataframe.drop(columns='weather', inplace=True, errors='ignore')
    dataframe.drop(index=dataframe.loc[start_time > dataframe['time'] > end_time].index, inplace=True, errors='ignore')
    dataframe['sensorId'] = sensor['sensorId']

    if not dataframe.empty:
        weather_data_path = path.join(DATA_EXTERNAL_PATH, city_name, sensor['sensorId'], 'weather.csv')
        save_dataframe(dataframe, 'weather', weather_data_path, sensor['sensorId'])
