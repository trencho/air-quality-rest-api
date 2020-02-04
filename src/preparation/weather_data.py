import json
import urllib

import pandas as pd
from pandas.io.json import json_normalize

from definitions import DATA_EXTERNAL_PATH

url = 'https://api.darksky.net/forecast/'
parameters = '?exclude=currently,minutely,daily,alerts,flags&extend=hourly'


def extract_weather_json(dark_sky_env, city, sensor_id, coordinates, start_time, end_time):
    dark_sky_json = json.load(dark_sky_env)
    private_key = dark_sky_json.get('private_key')
    link = url + '/' + private_key + '/' + coordinates + ',' + start_time
    request = link + parameters

    dataframe = pd.DataFrame()
    while start_time < end_time:
        with urllib.request.urlopen(request) as response:
            data = json.load(response)
        hourly = data.get('hourly')
        if hourly is not None:
            df = json_normalize(hourly['data'])
            start_time = df['date'].iloc[-1]
            dataframe = dataframe.append(df, sort=True)

        link = url + '/' + private_key + '/' + coordinates + ',' + start_time
        request = link + parameters

    dataframe.to_csv(DATA_EXTERNAL_PATH + '/' + city + '/' + sensor_id + '/weather_report.csv', index=False)
