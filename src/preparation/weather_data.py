import traceback
from json import load as json_load
from os import environ, path

from pandas import DataFrame, json_normalize
from requests import get as requests_get

from definitions import DATA_EXTERNAL_PATH, dark_sky_env_value, hour_in_secs
from .handle_data import save_dataframe


def extract_weather_json(city_name, sensor, start_time, end_time):
    url = 'https://api.darksky.net/forecast'
    params = 'exclude=currently,minutely,daily,alerts,flags&extend=hourly'
    dark_sky_env = environ.get(dark_sky_env_value)
    with open(dark_sky_env) as dark_sky_file:
        dark_sky_json = json_load(dark_sky_file)
    private_key = dark_sky_json.get('private_key')
    link = url + '/' + private_key + '/' + sensor['position'] + ',' + str(start_time)

    dataframe = DataFrame()
    while start_time < end_time:
        with requests_get(url=link, params=params) as weather_response:
            try:
                weather_json = weather_response.json()
                hourly = weather_json.get('hourly')
                df = json_normalize(hourly.get('data'))
                df.sort_values(by='time', inplace=True)
                last_timestamp = df['time'].iloc[-1]
                if start_time < last_timestamp:
                    start_time = last_timestamp
                else:
                    start_time += hour_in_secs
                dataframe = dataframe.append(df, ignore_index=True, sort=True)
            except ValueError:
                print(weather_response)
                print(traceback.format_exc())
                start_time += hour_in_secs

        link = url + '/' + private_key + '/' + sensor['position'] + ',' + str(start_time)

    if not dataframe.empty:
        weather_data_path = path.join(DATA_EXTERNAL_PATH, city_name, sensor['sensorId'], 'weather_report.csv')
        save_dataframe(dataframe, 'weather', weather_data_path, sensor['sensorId'])
