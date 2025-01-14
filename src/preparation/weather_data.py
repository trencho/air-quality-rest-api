from logging import getLogger
from os import environ, path
from time import sleep

from pandas import DataFrame, json_normalize
from requests import get, RequestException

from definitions import DARK_SKY_TOKEN, DATA_PATH, DATA_RAW_PATH, FORECAST_COUNTER, ONECALL_COUNTER, \
    OPEN_WEATHER_TOKEN, REQUESTS_LIMIT
from processing import flatten_json, save_dataframe

logger = getLogger(__name__)


def check_counter(counter_name: str) -> bool:
    try:
        with open(path.join(DATA_PATH, f"{counter_name}.txt"), "r") as in_file:
            if int(next(in_file)) < REQUESTS_LIMIT:
                return True
            return False
    except OSError:
        return True


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
            save_dataframe(dataframe, "weather",
                           path.join(DATA_RAW_PATH, city_name, sensor["sensorId"], "weather.csv"), sensor["sensorId"])
    except Exception:
        logger.error(f"Error occurred while fetching DarkSky data for {city_name} - {sensor['sensorId']}",
                     exc_info=True)


def fetch_open_weather_data(city_name: str, sensor: dict) -> None:
    url = "https://api.openweathermap.org/data/3.0/onecall"
    sensor_position = sensor["position"].split(",")
    lat, lon = float(sensor_position[0]), float(sensor_position[1])
    units = "metric"
    exclude = "alerts,current,daily,minutely"
    token = environ[OPEN_WEATHER_TOKEN]
    params = f"lat={lat}&lon={lon}&units={units}&exclude={exclude}&appid={token}"

    try:
        weather_response = get(url, params)
        increment_counter(ONECALL_COUNTER)
        if weather_response.status_code >= 400:
            lock_counter(ONECALL_COUNTER)
            raise RequestException(f"The weather response returned content: {weather_response.text}")
        hourly_data = weather_response.json()["hourly"]
        dataframe = json_normalize([flatten_json(hourly) for hourly in hourly_data])

        if len(dataframe.index) > 0:
            save_dataframe(dataframe, "weather", path.join(DATA_RAW_PATH, city_name, sensor["sensorId"], "weather.csv"),
                           sensor["sensorId"])
    except Exception:
        logger.error(f"Error occurred while fetching Open Weather data for {city_name} - {sensor['sensorId']}",
                     exc_info=True)
        lock_counter(ONECALL_COUNTER)
    finally:
        sleep(1)


def fetch_pollution_data(city_name: str, sensor: dict) -> None:
    url = "https://api.openweathermap.org/data/2.5/air_pollution/forecast"
    sensor_position = sensor["position"].split(",")
    lat, lon = float(sensor_position[0]), float(sensor_position[1])
    token = environ[OPEN_WEATHER_TOKEN]
    params = f"lat={lat}&lon={lon}&appid={token}"

    try:
        pollution_response = get(url, params)
        increment_counter(FORECAST_COUNTER)
        if pollution_response.status_code >= 400:
            lock_counter(FORECAST_COUNTER)
            raise RequestException(f"The pollution response returned content: {pollution_response.text}")
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
        logger.error(f"Error occurred while fetching pollution data for {city_name} - {sensor["sensorId"]}",
                     exc_info=True)
        lock_counter(FORECAST_COUNTER)
    finally:
        sleep(1)


def fetch_weather_data(city_name: str, sensor: dict) -> None:
    if check_counter(ONECALL_COUNTER):
        fetch_open_weather_data(city_name, sensor)

    if check_counter(FORECAST_COUNTER):
        fetch_pollution_data(city_name, sensor)


def increment_counter(counter_name: str) -> None:
    counter = 0
    onecall_path = path.join(DATA_PATH, f"{counter_name}.txt")
    try:
        with open(onecall_path, "r") as in_file:
            counter = int(next(in_file))
            counter += 1
    except OSError:
        logger.error("Error occurred while incrementing the API counter", exc_info=True)
    with open(onecall_path, "w") as out_file:
        out_file.write(str(counter))


def lock_counter(counter_name: str) -> None:
    onecall_path = path.join(DATA_PATH, f"{counter_name}.txt")
    with open(onecall_path, "w") as out_file:
        out_file.write(str(REQUESTS_LIMIT))
