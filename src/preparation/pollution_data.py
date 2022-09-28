from os import environ, path
from time import sleep

from pandas import DataFrame
from requests import get

from api.config.logger import log
from definitions import DATA_RAW_PATH, open_weather_token
from processing import save_dataframe


def fetch_pollution_data(city_name: str, sensor: dict) -> None:
    url = "https://api.openweathermap.org/data/2.5/air_pollution/forecast"
    sensor_position = sensor["position"].split(",")
    lat, lon = float(sensor_position[0]), float(sensor_position[1])
    token = environ[open_weather_token]
    params = f"lat={lat}&lon={lon}&appid={token}"

    try:
        pollution_response = get(url, params)
        pollution_data = pollution_response.json()["list"]
        data = []
        for pollution in pollution_data:
            pollution_dict = {"time": pollution["dt"]}
            pollution_dict.update(pollution["main"])
            pollution_dict.update(pollution["components"])
            data.append(pollution_dict)
        dataframe = DataFrame(data)

        if len(dataframe.index) > 0:
            save_dataframe(dataframe, "pollution",
                           path.join(DATA_RAW_PATH, city_name, sensor["sensorId"], "pollution.csv"), sensor["sensorId"])
    except Exception:
        log.error(f"Error occurred while fetching pollution data for {city_name} - {sensor['sensorId']}", exc_info=1)
    finally:
        sleep(1)
