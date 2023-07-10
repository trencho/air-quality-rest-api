from os import makedirs, path

from flask import jsonify, Response
from pandas import DataFrame
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from definitions import DATA_PROCESSED_PATH, DATA_RAW_PATH
from preparation import fetch_weather_data
from processing import read_csv_in_chunks


@cache.memoize(timeout=3600)
def fetch_dataframe(city_name: str, sensor_id: str, collection: str) -> DataFrame | tuple[Response, int]:
    try:
        if (dataframe := read_csv_in_chunks(
                path.join(DATA_PROCESSED_PATH, city_name, sensor_id, f"{collection}.csv"))) is not None:
            return dataframe

        raise Exception
    except Exception:
        return jsonify(
            error_message="Cannot return historical data because the data is missing for that city and sensor."), \
            HTTP_404_NOT_FOUND


def create_data_paths(city_name: str, sensor_id: str) -> None:
    makedirs(path.join(DATA_RAW_PATH, city_name, sensor_id), exist_ok=True)
    makedirs(path.join(DATA_PROCESSED_PATH, city_name, sensor_id), exist_ok=True)


def fetch_city_data(city_name: str, sensor: dict) -> None:
    create_data_paths(city_name, sensor["sensorId"])
    fetch_weather_data(city_name, sensor)
