from os import environ, path
from time import sleep

from pandas import DataFrame, json_normalize
from requests import get

from api.config.logger import logger
from definitions import DARK_SKY_TOKEN, DATA_PATH, DATA_RAW_PATH, OPEN_WEATHER_TOKEN
from processing import flatten_json, save_dataframe


def fetch_dark_sky_data(city_name: str, sensor: dict) -> None:
    token = environ[DARK_SKY_TOKEN]
    url = f"https://api.darksky.net/forecast/{token}/{sensor['position']}"
    exclude = "currently,minutely,daily,alerts,flags"
    extend = "hourly"
    units = "si"
    params = f"exclude={exclude}&extend={extend}&units={units}"

    try:
        weather_response = get(url, params)
        hourly = weather_response.json()["hourly"]
        dataframe = json_normalize(hourly["data"])

        if len(dataframe.index) > 0:
            save_dataframe(dataframe, "weather", path.join(DATA_RAW_PATH, city_name, sensor["sensorId"], "weather.csv"),
                           sensor["sensorId"])
    except Exception:
        logger.error(f"Error occurred while fetching DarkSky data for {city_name} - {sensor['sensorId']}",
                     exc_info=True)


def fetch_open_weather_data(city_name: str, sensor: dict) -> None:
    url = "https://api.openweathermap.org/data/2.5/onecall"
    sensor_position = sensor["position"].split(",")
    lat, lon = float(sensor_position[0]), float(sensor_position[1])
    units = "metric"
    exclude = "alerts,current,daily,minutely"
    token = environ[OPEN_WEATHER_TOKEN]
    params = f"lat={lat}&lon={lon}&units={units}&exclude={exclude}&appid={token}"

    try:
        weather_response = get(url, params)
        hourly_data = weather_response.json()["hourly"]
        dataframe = json_normalize([flatten_json(hourly) for hourly in hourly_data])

        if len(dataframe.index) > 0:
            save_dataframe(dataframe, "weather", path.join(DATA_RAW_PATH, city_name, sensor["sensorId"], "weather.csv"),
                           sensor["sensorId"])
    except Exception:
        logger.error(f"Error occurred while fetching Open Weather data for {city_name} - {sensor['sensorId']}",
                     exc_info=True)


def fetch_pollution_data(city_name: str, sensor: dict) -> None:
    url = "https://api.openweathermap.org/data/2.5/air_pollution/forecast"
    sensor_position = sensor["position"].split(",")
    lat, lon = float(sensor_position[0]), float(sensor_position[1])
    token = environ[OPEN_WEATHER_TOKEN]
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
        logger.error(f"Error occurred while fetching pollution data for {city_name} - {sensor['sensorId']}",
                     exc_info=True)
    finally:
        sleep(1)


def fetch_weather_data(city_name: str, sensor: dict) -> None:
    fetch_open_weather_data(city_name, sensor)
    increment_counter("onecall_counter")

    fetch_pollution_data(city_name, sensor)
    increment_counter("forecast_counter")

    sleep(1)


def increment_counter(counter_name: str):
    counter = 0
    if path.exists(onecall_path := path.join(DATA_PATH, f"{counter_name}.txt")):
        with open(onecall_path, "r") as in_file:
            counter = int(next(in_file))
            counter += 1
    with open(onecall_path, "w") as out_file:
        out_file.write(str(counter))
