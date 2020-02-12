import json

import pandas as pd
import requests
from pandas import json_normalize

from definitions import DATA_EXTERNAL_PATH

url = 'https://api.darksky.net/forecast/'
parameters = '?exclude=currently,minutely,daily,alerts,flags&extend=hourly'

week_in_secs = 604800


def extract_weather_json(dark_sky_env, city, sensor, start_time, end_time):
    dark_sky_json = json.load(dark_sky_env)
    private_key = dark_sky_json.get('private_key')
    link = url + '/' + private_key + '/' + sensor['position'] + ',' + start_time
    request = link + parameters

    dataframe = pd.DataFrame()
    while start_time < end_time:
        with requests.get(request) as response:
            try:
                data = response.json()
                hourly = data.get('hourly')
                df = json_normalize(hourly['data'])
                start_time = df['date'].iloc[-1]
                dataframe = dataframe.append(df, sort=True)
            except ValueError:
                start_time += week_in_secs

        link = url + '/' + private_key + '/' + sensor['position'] + ',' + start_time
        request = link + parameters

    dataframe.to_csv(DATA_EXTERNAL_PATH + '/' + city + '/' + sensor['sensorId'] + '/weather_report.csv', index=False)
