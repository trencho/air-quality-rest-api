from base64 import b64encode
from datetime import datetime
from json import dump, load
from logging import getLogger
from os import environ, makedirs, path, remove, rmdir, walk
from shutil import unpack_archive

from apscheduler import Scheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import create_engine

from api.blueprints import fetch_city_data
from definitions import COLLECTIONS, DATA_EXTERNAL_PATH, DATA_PATH, DATA_PROCESSED_PATH, DATA_RAW_PATH, \
    FORECAST_COUNTER, MODELS_PATH, ONECALL_COUNTER, POLLUTANTS, REPO_NAME
from modeling import train_regression_model
from preparation import fetch_cities, fetch_countries, fetch_sensors, read_cities, read_sensors
from processing import current_hour, fetch_forecast_result, process_data, read_csv_in_chunks, save_dataframe
from .cache import cache
from .dump import generate_sql_dump
from .git import append_commit_files, create_archive, update_git_files
from .repository import RepositorySingleton

logger = getLogger(__name__)

DATABASE_FILE = path.join(DATA_PATH, "jobs.sqlite")

repository = RepositorySingleton.get_instance().get_repository()


def dump_data() -> None:
    file_list, file_names = [], []
    for root, directories, files in walk(DATA_PATH):
        if not directories and files:
            file_path = f"{root}.zip"
            create_archive(source=root, destination=file_path)
            with open(file_path, "rb") as in_file:
                data = b64encode(in_file.read())
            append_commit_files(file_list, data, path.dirname(path.abspath(root)), path.basename(file_path), file_names)
            remove(file_path)

    if file_list:
        update_git_files(file_list, file_names, environ[REPO_NAME], "master",
                         f"Scheduled data dump - {datetime.now().strftime("%H:%M:%S %d-%m-%Y")}")


def dump_jobs() -> None:
    current_time = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
    dump_filename = f"job_dump_{current_time}.sql"
    dump_content = generate_sql_dump(DATABASE_FILE)

    dump_path = path.join(DATA_PATH, dump_filename)
    with open(dump_path, 'w') as f:
        f.write(dump_content)


def fetch_hourly_data() -> None:
    for city in cache.get("cities") or read_cities():
        for sensor in read_sensors(city["cityName"]):
            fetch_city_data(city["cityName"], sensor)
            for collection in COLLECTIONS:
                if path.exists(path.join(DATA_RAW_PATH, city["cityName"], sensor["sensorId"], f"{collection}.csv")):
                    process_data(city["cityName"], sensor["sensorId"], collection)


def fetch_locations() -> None:
    cities = fetch_cities()
    with open(path.join(DATA_RAW_PATH, "cities.json"), "w") as out_file:
        dump(cities, out_file, indent=4)
    cache.set("cities", cities)
    countries = fetch_countries()
    with open(path.join(DATA_RAW_PATH, "countries.json"), "w") as out_file:
        dump(countries, out_file, indent=4)
    cache.set("countries", countries)
    for country in countries:
        try:
            repository.save(collection_name="countries", filter={"countryCode": country["countryCode"]}, item=country)
        except Exception:
            logger.error(f"Error occurred while updating data for {country['countryName']}", exc_info=True)

    sensors = {}
    for city in cities:
        try:
            repository.save(collection_name="cities", filter={"cityName": city["cityName"]}, item=city)
        except Exception:
            logger.error(f"Error occurred while updating data for {city['cityName']}", exc_info=True)
        sensors[city["cityName"]] = fetch_sensors(city["cityName"])
        for sensor in sensors[city["cityName"]]:
            sensor["cityName"] = city["cityName"]
            try:
                repository.save(collection_name="sensors", filter={"sensorId": sensor["sensorId"]}, item=sensor)
            except Exception:
                logger.error(f"Error occurred while updating data for {sensor['sensorId']}", exc_info=True)
        makedirs(path.join(DATA_RAW_PATH, city["cityName"]), exist_ok=True)
        with open(path.join(DATA_RAW_PATH, city["cityName"], "sensors.json"), "w") as out_file:
            dump(sensors[city["cityName"]], out_file, indent=4)


def import_data() -> None:
    for root, directories, files in walk(DATA_EXTERNAL_PATH):
        for file in files:
            file_path = path.join(root, file)
            if file.endswith(".zip"):
                fmt = str(path.basename(file_path).split(".")[1])
                unpack_archive(filename=file_path, extract_dir=root, format=fmt)
                remove(file_path)

    for root, directories, files in walk(DATA_EXTERNAL_PATH):
        for file in files:
            if not file.endswith(".csv"):
                continue

            file_path = path.join(root, file)
            try:
                dataframe = read_csv_in_chunks(file_path)
                save_dataframe(dataframe, path.splitext(file)[0],
                               path.join(DATA_RAW_PATH, path.relpath(file_path, DATA_EXTERNAL_PATH)),
                               path.basename(path.dirname(file_path)))
                remove(file_path)
            except Exception:
                logger.error(f"Error occurred while importing data from {file_path}", exc_info=True)

        if not directories and not files:
            rmdir(root)

    makedirs(DATA_EXTERNAL_PATH, exist_ok=True)


def model_training() -> None:
    for city in cache.get("cities") or read_cities():
        for sensor in read_sensors(city["cityName"]):
            for pollutant in POLLUTANTS:
                train_regression_model(city, sensor, pollutant)


def predict_locations() -> None:
    for city in cache.get("cities") or read_cities():
        for sensor in read_sensors(city["cityName"]):
            try:
                with open(file_path := path.join(DATA_PROCESSED_PATH, city["cityName"], sensor["sensorId"],
                                                 "predictions.json"), "r") as in_file:
                    repository.save(collection_name="predictions",
                                    filter={"cityName": city["cityName"], "sensorId": sensor["sensorId"]},
                                    item={"data": load(in_file), "cityName": city["cityName"],
                                          "sensorId": sensor["sensorId"]})
            except Exception:
                logger.error(f"Error occurred while updating forecast values from {file_path}", exc_info=True)

    for city in cache.get("cities") or read_cities():
        for sensor in read_sensors(city["cityName"]):
            try:
                forecast_result = fetch_forecast_result(city, sensor)
                with open(path.join(DATA_PROCESSED_PATH, city["cityName"], sensor["sensorId"], "predictions.json"),
                          "w") as out_file:
                    dump(list(forecast_result.values()), out_file, indent=4, default=str)
            except Exception:
                logger.error(
                    f"Error occurred while fetching forecast values for {city['cityName']} - {sensor['sensorId']}",
                    exc_info=True)


def reset_api_counter() -> None:
    try:
        with open(path.join(DATA_PATH, f"{FORECAST_COUNTER}.txt"), "w") as out_file:
            out_file.write(str(0))
        with open(path.join(DATA_PATH, f"{ONECALL_COUNTER}.txt"), "w") as out_file:
            out_file.write(str(0))
    except OSError:
        logger.error("Error occurred while resetting the API counter", exc_info=True)


def reset_model_lock() -> None:
    for file in [path.join(root, file) for root, directories, files in walk(MODELS_PATH) for file in files if
                 file.endswith(".lock")]:
        last_modified = int(path.getmtime(file))
        if last_modified < int(datetime.timestamp(current_hour())) - 3600:
            remove(path.join(MODELS_PATH, file))


def configure_scheduler() -> None:
    db_url = f"sqlite:////{DATABASE_FILE}"
    engine = create_engine(db_url)
    data_store = SQLAlchemyDataStore(engine)
    scheduler = Scheduler(data_store)
    schedule_jobs(scheduler)
    scheduler.start_in_background()


def schedule_jobs(scheduler: Scheduler) -> None:
    scheduler.add_schedule(func_or_task_id=dump_data, trigger=CronTrigger(day="*/15"), id="dump_data",
                           misfire_grace_time=None)
    scheduler.add_schedule(func_or_task_id=dump_jobs, trigger=CronTrigger(hour=0), id="dump_jobs",
                           misfire_grace_time=None)
    scheduler.add_schedule(func_or_task_id=fetch_hourly_data, trigger=CronTrigger(hour="*/2"), id="fetch_hourly_data",
                           misfire_grace_time=None)
    scheduler.add_schedule(func_or_task_id=fetch_locations, trigger=CronTrigger(hour=0), id="fetch_locations",
                           misfire_grace_time=None)
    scheduler.add_schedule(func_or_task_id=import_data, trigger=CronTrigger(hour=0), id="import_data",
                           misfire_grace_time=None)
    scheduler.add_schedule(func_or_task_id=predict_locations, trigger=CronTrigger(minute=0), id="predict_locations",
                           misfire_grace_time=None)
    scheduler.add_schedule(func_or_task_id=reset_api_counter, trigger=CronTrigger(hour=0), id="reset_api_counter",
                           misfire_grace_time=None)
    scheduler.add_schedule(func_or_task_id=reset_model_lock, trigger=CronTrigger(hour=0), id="reset_model_lock",
                           misfire_grace_time=None)
