from json import load as json_load
from os import environ, path
from traceback import format_exc

from pandas import DataFrame, json_normalize
from requests import get as requests_get

from definitions import DATA_EXTERNAL_PATH, dark_sky_env_value, hour_in_secs
from .handle_data import save_dataframe


def fetch_weather_data(city_name, sensor, start_time, end_time):
    url = 'https://api.darksky.net/forecast'
    params = 'exclude=currently,minutely,daily,alerts,flags&extend=hourly'
    dark_sky_env = environ[dark_sky_env_value]
    with open(dark_sky_env) as dark_sky_file:
        dark_sky_json = json_load(dark_sky_file)
    private_key = dark_sky_json['private_key']
    link = f'{url}/{private_key}/{sensor["position"]},{start_time}'

    dataframe = DataFrame()
    while start_time < end_time:
        weather_response = requests_get(url=link, params=params)
        try:
            weather_json = weather_response.json()
            hourly = weather_json['hourly']
            df = json_normalize(hourly['data'])
            df.sort_values(by='time', inplace=True)
            last_timestamp = df['time'].iloc[-1]
            if start_time < last_timestamp:
                start_time = last_timestamp
            else:
                start_time += hour_in_secs
            dataframe = dataframe.append(df, ignore_index=True)
        except (KeyError, ValueError):
            print(weather_response)
            print(format_exc())
            start_time += hour_in_secs

        link = f'{url}/{private_key}/{sensor["position"]},{start_time}'

    dataframe.drop(index=dataframe.loc[dataframe['time'] > end_time].index, inplace=True, errors='ignore')
    if not dataframe.empty:
        weather_data_path = path.join(DATA_EXTERNAL_PATH, city_name, sensor['sensorId'], 'weather.csv')
        save_dataframe(dataframe, 'weather', weather_data_path, sensor['sensorId'])
