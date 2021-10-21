from os import environ, path
from time import sleep
from traceback import print_exc

from pandas import DataFrame
from requests import get

from definitions import DATA_RAW_PATH, open_weather_token
from .handle_data import save_dataframe


def fetch_pollution_data(city_name: str, sensor: dict) -> None:
    url = 'https://api.openweathermap.org/data/2.5/air_pollution/forecast'
    sensor_position = sensor['position'].split(',')
    lat, lon = float(sensor_position[0]), float(sensor_position[1])
    token = environ[open_weather_token]
    params = f'lat={lat}&lon={lon}&appid={token}'

    dataframe = DataFrame()
    try:
        pollution_response = get(url, params)
        pollution_data = pollution_response.json()['list']
        data = []
        for pollution in pollution_data:
            pollution_dict = {'time': pollution['dt']}
            pollution_dict.update(pollution['main'])
            pollution_dict.update(pollution['components'])
            data.append(pollution_dict)
        dataframe = dataframe.append(DataFrame(data), ignore_index=True)

        if len(dataframe.index) > 0:
            data_path = path.join(DATA_RAW_PATH, city_name, sensor['sensorId'], 'pollution.csv')
            save_dataframe(dataframe, 'pollution', data_path, sensor['sensorId'])
    except Exception:
        print_exc()
    finally:
        sleep(1)
