import json
import os
import urllib

import pandas as pd
from pandas.io.json import json_normalize

from definitions import DATA_EXTERNAL_PATH
from definitions import stations

url = 'https://api.darksky.net/forecast/'
parameters = '?exclude=currently,minutely,daily,alerts,flags&extend=hourly'

day_in_secs = 82800


def extract_json(station, timestamp):
    dark_sky_env = os.environ.get('DarkSkyAPI')
    if dark_sky_env is None:
        print('Please set the environment variable DarkSkyAPI')
        return

    dark_sky_json = json.load(dark_sky_env)
    private_key = dark_sky_json.get('private_key')
    coordinates = stations[station]
    link = url + '/' + private_key + '/' + coordinates + ',' + timestamp
    request = link + parameters

    dataframe = pd.DataFrame()
    for i in range(1525):
        with urllib.request.urlopen(request) as response:
            data = json.load(response)
        hourly = data.get('hourly')
        if hourly is not None:
            df = json_normalize(hourly['data'])
            dataframe = dataframe.append(df, sort=True)

        timestamp += day_in_secs
        link = url + '/' + private_key + '/' + coordinates + ',' + timestamp
        request = link + parameters

    dataframe.to_csv(DATA_EXTERNAL_PATH + '/weather/' + station + '.csv', index=False)


def weather_data_api(station=None, hour='1420066800'):
    if station is not None:
        extract_json(station, hour)
    else:
        for station in stations:
            extract_json(station, hour)
