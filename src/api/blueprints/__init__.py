from os import makedirs, path

from flask import jsonify, make_response, Response
from pandas import DataFrame
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from definitions import DATA_PROCESSED_PATH, DATA_RAW_PATH
from preparation import fetch_dark_sky_data, fetch_pollution_data
from processing import read_csv_in_chunks
from processing.merge_data import merge_air_quality_data


@cache.memoize(timeout=3600)
def fetch_dataframe(city_name: str, sensor_id: str, collection: str) -> [DataFrame, Response]:
    try:
        if (dataframe := read_csv_in_chunks(
                path.join(DATA_PROCESSED_PATH, city_name, sensor_id, f'{collection}.csv'))) is not None:
            return dataframe

        raise Exception
    except Exception:
        message = 'Cannot return historical data because the data is missing for that city and sensor.'
        return make_response(jsonify(error_message=message), HTTP_404_NOT_FOUND)


def create_data_paths(city_name: str, sensor_id: str) -> None:
    makedirs(path.join(DATA_RAW_PATH, city_name, sensor_id), exist_ok=True)
    makedirs(path.join(DATA_PROCESSED_PATH, city_name, sensor_id), exist_ok=True)


def fetch_city_data(city_name: str, sensor: dict) -> None:
    create_data_paths(city_name, sensor['sensorId'])

    fetch_dark_sky_data(city_name, sensor)
    fetch_pollution_data(city_name, sensor)
    merge_air_quality_data(DATA_RAW_PATH, city_name, sensor['sensorId'])
