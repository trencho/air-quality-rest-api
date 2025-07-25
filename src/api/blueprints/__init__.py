from logging import getLogger
from os import makedirs
from pathlib import Path

from flask import jsonify, Response
from pandas import DataFrame
from starlette.status import HTTP_404_NOT_FOUND

from api.config.cache import cache
from definitions import CACHE_TIMEOUTS, DATA_PROCESSED_PATH, DATA_RAW_PATH
from preparation import check_api_lock, fetch_weather_data
from processing import read_csv_in_chunks

logger = getLogger(__name__)


@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
def fetch_dataframe(
    data_path: Path, collection: str
) -> DataFrame | tuple[Response, int]:
    try:
        if (
            dataframe := read_csv_in_chunks(
                DATA_PROCESSED_PATH / data_path / f"{collection}.csv"
            )
        ) is not None:
            return dataframe

        raise Exception
    except Exception:
        logger.exception(
            f"Exception while reading data from CSV file from {data_path} - {collection}",
        )
        return (
            jsonify(
                error_message="Cannot return historical data because the data is missing for that city and sensor."
            ),
            HTTP_404_NOT_FOUND,
        )


def create_data_paths(city_name: str, sensor_id: str) -> None:
    makedirs(DATA_RAW_PATH / city_name / sensor_id, exist_ok=True)
    makedirs(DATA_PROCESSED_PATH / city_name / sensor_id, exist_ok=True)


def fetch_city_data(city_name: str, sensor: dict) -> None:
    if check_api_lock():
        return
    create_data_paths(city_name, sensor["sensorId"])
    fetch_weather_data(city_name, sensor)
