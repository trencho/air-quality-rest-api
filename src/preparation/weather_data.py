import json
import traceback

import pandas as pd
import requests
from pandas import json_normalize

from definitions import DATA_EXTERNAL_PATH
from preparation.save_data import save_dataframe

url = 'https://api.darksky.net/forecast'
params = 'exclude=currently,minutely,daily,alerts,flags&extend=hourly'

hour_in_secs = 3600


def extract_weather_json(dark_sky_env, city_name, sensor, start_time, end_time):
    with open(dark_sky_env) as dark_sky_file:
        dark_sky_json = json.load(dark_sky_file)
    private_key = dark_sky_json.get('private_key')
    link = url + '/' + private_key + '/' + sensor['position'] + ',' + str(start_time)

    dataframe = pd.DataFrame()
    while start_time < end_time:
        with requests.get(url=link, params=params) as weather_response:
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

    weather_data_path = DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/weather_report.csv'
    save_dataframe(dataframe, 'weather', weather_data_path)
