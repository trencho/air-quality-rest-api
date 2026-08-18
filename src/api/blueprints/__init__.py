from logging import getLogger
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
        dataframe = read_csv_in_chunks(
            DATA_PROCESSED_PATH / data_path / f"{collection}.csv"
        )
    except (OSError, ValueError) as error:
        # OSError covers the file being absent or unreadable; ValueError covers pandas
        # refusing its contents, including the `concat` of an empty chunk list. Anything
        # outside those two is a defect in this service rather than missing data, and it
        # should reach the error handler instead of being answered with a 404.
        logger.warning(
            "Could not read the %s data for %s: %s", collection, data_path, error
        )
        dataframe = None

    if dataframe is not None:
        return dataframe

    # read_csv_in_chunks returns None for a file that parsed but held no usable rows. That
    # used to be signalled by raising a bare Exception into the handler above purely to
    # reach this return, which logged a manufactured traceback for the ordinary case of a
    # city having no history yet. It is a plain branch now, and it says which case it is.
    logger.info("No %s data available for %s", collection, data_path)
    return (
        jsonify(
            error_message="Cannot return historical data because the data is missing for that city and sensor."
        ),
        HTTP_404_NOT_FOUND,
    )


def create_data_paths(city_name: str, sensor_id: str) -> None:
    (DATA_RAW_PATH / city_name / sensor_id).mkdir(parents=True, exist_ok=True)
    (DATA_PROCESSED_PATH / city_name / sensor_id).mkdir(parents=True, exist_ok=True)


def fetch_city_data(city_name: str, sensor: dict) -> None:
    if check_api_lock():
        return
    create_data_paths(city_name, sensor["sensorId"])
    fetch_weather_data(city_name, sensor)
