from os import environ, makedirs, path

from pandas import DataFrame

from definitions import COLLECTIONS, DATA_EXTERNAL_PATH, DATA_PROCESSED_PATH, DATA_RAW_PATH, ENVIRONMENT_VARIABLES, \
    LOG_PATH, MODELS_PATH, RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH
from preparation import read_cities, read_sensors
from processing import find_missing_data, read_csv_in_chunks, save_dataframe
from .logger import logger
from .repository import RepositorySingleton
from .schedule import fetch_locations

SYSTEM_PATHS = [
    DATA_EXTERNAL_PATH,
    DATA_PROCESSED_PATH,
    DATA_RAW_PATH,
    LOG_PATH,
    MODELS_PATH,
    RESULTS_ERRORS_PATH,
    RESULTS_PREDICTIONS_PATH
]

repository = RepositorySingleton.get_instance().get_repository()


def check_environment_variables() -> None:
    for environment_variable in ENVIRONMENT_VARIABLES:
        if environ.get(environment_variable) is None:
            logger.error(f"The environment variable \"{environment_variable}\" is missing")
            exit(-1)


def fetch_collection(collection: str, city_name: str, sensor_id: str) -> None:
    db_records = DataFrame(
        repository.get_many(collection_name=collection, filter={"sensorId": sensor_id},
                            projection={"_id": False, "sensorId": False}))
    if len(db_records.index) == 0:
        return

    collection_dir = path.join(DATA_RAW_PATH, city_name, sensor_id)
    makedirs(collection_dir, exist_ok=True)
    collection_path = path.join(collection_dir, f"{collection}.csv")
    try:
        dataframe = read_csv_in_chunks(collection_path)
        new_db_records = find_missing_data(db_records, dataframe, "time")
        new_db_records.to_csv(collection_path, header=False, index=False, mode="a")

        save_dataframe(dataframe, collection, collection_path, sensor_id)
    except Exception:
        logger.error(f"Could not fetch data from local storage for {city_name} - {sensor_id} - {collection}",
                     exc_info=True)
        db_records.to_csv(collection_path, index=False)


def fetch_db_data() -> None:
    for city in read_cities():
        for sensor in read_sensors(city["cityName"]):
            for collection in COLLECTIONS:
                try:
                    fetch_collection(collection, city["cityName"], sensor["sensorId"])
                except Exception:
                    logger.error(
                        f"Could not fetch data from the database for {city['cityName']} - {sensor['sensorId']} - "
                        f"{collection}", exc_info=True)


def fetch_data() -> None:
    fetch_locations()
    fetch_db_data()


def init_system_paths() -> None:
    for system_path in SYSTEM_PATHS:
        makedirs(system_path, exist_ok=True)
