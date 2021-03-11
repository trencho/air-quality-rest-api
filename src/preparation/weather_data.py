from os import environ, path
from traceback import format_exc

from pandas import DataFrame, json_normalize
from requests import get as requests_get

from definitions import DATA_EXTERNAL_PATH, dark_sky_token
from .handle_data import save_dataframe

day_in_seconds = 86400


def fetch_weather_data(city_name, sensor, start_time, end_time):
    domain = 'https://api.darksky.net'
    token = environ[dark_sky_token]
    url = f'{domain}/forecast/{token}/{sensor["position"]},{start_time}'
    exclude = 'currently,minutely,daily,alerts,flags'
    extend = 'hourly'
    params = f'exclude={exclude}&extend={extend}'

    dataframe = DataFrame()
    while start_time < end_time:
        weather_response = requests_get(url=url, params=params)
        try:
            weather_json = weather_response.json()
            hourly = weather_json['hourly']
            df = json_normalize(hourly['data'])
            df.sort_values(by='time', inplace=True)
            last_timestamp = df['time'].iloc[-1]
            if start_time < last_timestamp:
                start_time = last_timestamp
            else:
                start_time += day_in_seconds
            dataframe = dataframe.append(df, ignore_index=True)
        except (KeyError, ValueError):
            print(weather_response)
            print(format_exc())
            start_time += day_in_seconds

        url = f'{domain}/forecast/{token}/{sensor["position"]},{start_time}'

    dataframe.drop(index=dataframe.loc[start_time > dataframe['time'] > end_time].index, inplace=True, errors='ignore')
    dataframe['sensorId'] = sensor['sensorId']

    if not dataframe.empty:
        weather_data_path = path.join(DATA_EXTERNAL_PATH, city_name, sensor['sensorId'], 'weather.csv')
        save_dataframe(dataframe, 'weather', weather_data_path, sensor['sensorId'])
