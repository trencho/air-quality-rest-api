from datetime import datetime
from os import environ, path
from time import sleep
from traceback import format_exc

from pandas import DataFrame
from requests import get as requests_get

from definitions import DATA_EXTERNAL_PATH, open_weather_token
from processing import current_hour
from .handle_data import save_dataframe


def fetch_pollution_data(city_name, sensor):
    url = 'https://api.openweathermap.org/data/2.5/air_pollution'
    sensor_position = sensor['position'].split(',')
    lat, lon = float(sensor_position[0]), float(sensor_position[1])
    token = environ[open_weather_token]
    params = f'lat={lat}&lon={lon}&appid={token}'

    dataframe = DataFrame()
    pollution_response = requests_get(url=url, params=params)
    try:
        pollution_json = pollution_response.json()
        pollution_data = pollution_json['list']
        data = []
        for pollution in pollution_data:
            pollution_dict = {'time': pollution['dt']}
            pollution_dict.update(pollution['main'])
            pollution_dict.update(pollution['components'])
            data.append(pollution_dict)
        dataframe = dataframe.append(DataFrame(data), ignore_index=True)
    except ValueError:
        print(pollution_response)
        print(format_exc())

    sleep(1)

    current_datetime = current_hour(datetime.now())
    current_timestamp = int(datetime.timestamp(current_datetime))
    dataframe.drop(index=dataframe.loc[dataframe['time'] > current_timestamp].index, inplace=True, errors='ignore')

    if not dataframe.empty:
        dataframe['sensorId'] = sensor['sensorId']
        pollution_data_path = path.join(DATA_EXTERNAL_PATH, city_name, sensor['sensorId'], 'pollution.csv')
        save_dataframe(dataframe, 'pollution', pollution_data_path, sensor['sensorId'])
