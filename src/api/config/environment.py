from gc import collect
from logging import getLogger
from os import environ, makedirs

from pandas import DataFrame

from definitions import (
    COLLECTIONS,
    DATA_EXTERNAL_PATH,
    DATA_PROCESSED_PATH,
    DATA_RAW_PATH,
    ENVIRONMENT_VARIABLES,
    LOG_PATH,
    MODELS_PATH,
    RESULTS_ERRORS_PATH,
    RESULTS_PREDICTIONS_PATH,
)
from preparation import read_cities, read_sensors
from processing import find_missing_data, read_csv_in_chunks, save_dataframe
from .repository import RepositorySingleton
from .schedule import fetch_locations

logger = getLogger(__name__)

repository = RepositorySingleton.get_instance().get_repository()

SYSTEM_PATHS = [
    DATA_EXTERNAL_PATH,
    DATA_PROCESSED_PATH,
    DATA_RAW_PATH,
    LOG_PATH,
    MODELS_PATH,
    RESULTS_ERRORS_PATH,
    RESULTS_PREDICTIONS_PATH,
]


def init_environment_variables() -> None:
    missing_envs = []
    for environment_variable in ENVIRONMENT_VARIABLES:
        if environ.get(environment_variable) is None:
            missing_envs.append(environment_variable)

    if missing_envs:
        logger.error(f"Missing environment variables: {', '.join(missing_envs)}")
        exit(-1)


# TODO: Review this method for inserting duplicate values
def fetch_collection(collection: str, city_name: str, sensor_id: str) -> None:
    db_records = DataFrame(
        repository.get_many(
            collection_name=collection,
            filter={"sensorId": sensor_id},
            projection={"_id": False, "sensorId": False},
        )
    )
    if db_records.empty:
        return

    collection_dir = DATA_RAW_PATH / city_name / sensor_id
    makedirs(collection_dir, exist_ok=True)
    collection_path = collection_dir / f"{collection}.csv"
    try:
        dataframe = read_csv_in_chunks(collection_path)
        new_db_records = find_missing_data(db_records, dataframe, "time")
        # TODO: Review this line for converting column data types
        # new_db_records = new_db_records.astype(column_dtypes, errors="ignore")
        # combined_df = concat([dataframe, new_db_records]).drop_duplicates(subset="time", keep="last")
        # combined_df.to_csv(collection_path, index=False)
        # del combined_df
        new_db_records.to_csv(collection_path, header=False, index=False, mode="a")

        save_dataframe(dataframe, collection, collection_path, sensor_id)
        del dataframe
    except Exception:
        logger.exception(
            f"Could not fetch data from local storage for {city_name} - {sensor_id} - {collection}",
        )
        # TODO: Review this line for converting column data types
        # db_records = db_records.astype(column_dtypes, errors="ignore")
        db_records.to_csv(collection_path, index=False)
    finally:
        del db_records
        collect()


def fetch_db_data() -> None:
    for city in read_cities():
        for sensor in read_sensors(city["cityName"]):
            for collection in COLLECTIONS:
                try:
                    fetch_collection(collection, city["cityName"], sensor["sensorId"])
                except Exception:
                    logger.exception(
                        f"Could not fetch data from the database for {city['cityName']} - {sensor['sensorId']} - "
                        f"{collection}",
                    )


def init_data() -> None:
    fetch_locations()
    fetch_db_data()


def init_system_paths() -> None:
    for system_path in SYSTEM_PATHS:
        makedirs(system_path, exist_ok=True)
