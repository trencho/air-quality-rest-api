from atexit import register
from base64 import b64encode
from datetime import datetime
from json import dump, dumps, loads
from logging import getLogger
from os import environ, makedirs, remove, rmdir, walk
from pathlib import Path
from pickle import load
from shutil import unpack_archive

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine

from api.blueprints import fetch_city_data
from definitions import COLLECTIONS, DATA_EXTERNAL_PATH, DATA_PATH, DATA_PROCESSED_PATH, DATA_RAW_PATH, \
    MODELS_PATH, OPEN_WEATHER, POLLUTANTS, REPO_NAME
from modeling import train_regression_model
from preparation import check_api_lock, fetch_cities, fetch_countries, fetch_sensors, read_cities, read_sensors
from processing import current_hour, fetch_forecast_result, process_data, read_csv_in_chunks, save_dataframe
from .cache import cache
from .dump import generate_sql_dump
from .git import append_commit_files, create_archive, update_git_files
from .repository import RepositorySingleton

logger = getLogger(__name__)

scheduler = BackgroundScheduler()
jobstore_name = "aqra"
DATABASE_FILE = DATA_PATH / "jobs.sqlite"
REPO_BRANCH = "master"

repository = RepositorySingleton.get_instance().get_repository()


@scheduler.scheduled_job(trigger="cron", id="convert_pkl_to_json", misfire_grace_time=None, jobstore=jobstore_name,
                         minute="*/10")
def convert_pkl_to_json():
    for root, _, files in walk(MODELS_PATH):
        for file in files:
            if file.endswith(".pkl"):
                pkl_path = Path(root) / file
                json_path = Path(root) / file.replace(".pkl", ".json")
                try:
                    with open(pkl_path, "rb") as pkl_file:
                        data = load(pkl_file)
                    with open(json_path, "w") as json_file:
                        dump(data, json_file, indent=4, ensure_ascii=False)
                except Exception:
                    logger.error(f"Failed to convert {pkl_path}", exc_info=True)


@scheduler.scheduled_job(trigger="cron", id="dump_data", misfire_grace_time=None, jobstore=jobstore_name, day="*/15")
def dump_data() -> None:
    file_list, file_names = [], []
    for root, directories, files in walk(DATA_PATH):
        if not directories and files:
            file_path = f"{root}.zip"
            create_archive(source=root, destination=file_path)
            with open(file_path, "rb") as in_file:
                data = b64encode(in_file.read())
            append_commit_files(file_list, data, Path(root).resolve().parent, Path(file_path).name, file_names)
            remove(file_path)

    if file_list:
        update_git_files(file_list, file_names, environ[REPO_NAME], REPO_BRANCH,
                         f"Scheduled data dump - {datetime.now().strftime('%H:%M:%S %d-%m-%Y')}")


@scheduler.scheduled_job(trigger="cron", id="dump_jobs", misfire_grace_time=None, jobstore=jobstore_name, hour=0)
def dump_jobs() -> None:
    dump_filename = "job_dump.sql"
    dump_content = generate_sql_dump(DATABASE_FILE)

    dump_path = DATA_PATH / dump_filename
    dump_path.write_text(dump_content)


@scheduler.scheduled_job(trigger="cron", id="fetch_hourly_data", misfire_grace_time=None, jobstore=jobstore_name,
                         hour="*/2")
def fetch_hourly_data() -> None:
    if check_api_lock() is False:
        return
    for city in cache.get("cities") or read_cities():
        for sensor in read_sensors(city["cityName"]):
            fetch_city_data(city["cityName"], sensor)
            for collection in COLLECTIONS:
                if (DATA_RAW_PATH / city["cityName"] / sensor["sensorId"] / f"{collection}.csv").exists():
                    process_data(city["cityName"], sensor["sensorId"], collection)


@scheduler.scheduled_job(trigger="cron", id="fetch_locations", misfire_grace_time=None, jobstore=jobstore_name, hour=0)
def fetch_locations() -> None:
    countries = fetch_countries()
    (DATA_RAW_PATH / "countries.json").write_text(dumps(countries, indent=4))
    cache.set("countries", countries)
    for country in countries:
        try:
            repository.save(collection_name="countries", filter={"countryCode": country["countryCode"]}, item=country)
        except Exception:
            logger.error(f"Error occurred while updating data for {country['countryName']}", exc_info=True)

    cities = fetch_cities()
    (DATA_PATH / "cities.json").write_text(dumps(cities, indent=4))
    cache.set("cities", cities)
    for city in cities:
        try:
            repository.save(collection_name="cities", filter={"cityName": city["cityName"]}, item=city)
        except Exception:
            logger.error(f"Error occurred while updating data for {city['cityName']}", exc_info=True)
        sensors = fetch_sensors(city["cityName"])
        for sensor in sensors:
            sensor["cityName"] = city["cityName"]
            try:
                repository.save(collection_name="sensors", filter={"sensorId": sensor["sensorId"]}, item=sensor)
            except Exception:
                logger.error(f"Error occurred while updating data for {sensor['sensorId']}", exc_info=True)
        makedirs(DATA_RAW_PATH / city["cityName"], exist_ok=True)
        (DATA_RAW_PATH / city["cityName"] / "sensors.json").write_text(dumps(sensors, indent=4))


@scheduler.scheduled_job(trigger="cron", id="import_data", misfire_grace_time=None, jobstore=jobstore_name, hour=0)
def import_data() -> None:
    for root, _, files in walk(DATA_EXTERNAL_PATH):
        for file in files:
            file_path = Path(root) / file
            if file.endswith(".zip"):
                fmt = file_path.suffix.lstrip(".")
                unpack_archive(filename=file_path, extract_dir=root, format=fmt)
                remove(file_path)

    for root, directories, files in walk(DATA_EXTERNAL_PATH):
        for file in files:
            if not file.endswith(".csv"):
                continue

            file_path = Path(root) / file
            try:
                dataframe = read_csv_in_chunks(file_path)
                save_dataframe(dataframe, Path(file).stem, DATA_RAW_PATH / file_path.relative_to(DATA_EXTERNAL_PATH),
                               file_path.parent.name)
                remove(file_path)
            except Exception:
                logger.error(f"Error occurred while importing data from {file_path}", exc_info=True)

        if not directories and not files:
            rmdir(root)

    makedirs(DATA_EXTERNAL_PATH, exist_ok=True)


@scheduler.scheduled_job(trigger="cron", id="model_training", misfire_grace_time=None, jobstore=jobstore_name, minute=0)
def model_training() -> None:
    for city in cache.get("cities") or read_cities():
        for sensor in read_sensors(city["cityName"]):
            for pollutant in POLLUTANTS:
                logger.info(f"Training regression model for {city['cityName']} - {sensor['sensorId']} - {pollutant}")
                train_regression_model(city, sensor, pollutant)


@scheduler.scheduled_job(trigger="cron", id="predict_locations", misfire_grace_time=None, jobstore=jobstore_name,
                         minute=0)
def predict_locations() -> None:
    for city in cache.get("cities") or read_cities():
        for sensor in read_sensors(city["cityName"]):
            file_path = DATA_PROCESSED_PATH / city["cityName"] / sensor["sensorId"] / "predictions.json"
            try:
                repository.save(collection_name="predictions",
                                filter={"cityName": city["cityName"], "sensorId": sensor["sensorId"]},
                                item={"data": loads(file_path.read_text()), "cityName": city["cityName"],
                                      "sensorId": sensor["sensorId"]})
            except Exception:
                logger.error(f"Error occurred while updating forecast values from {file_path}", exc_info=True)

    for city in cache.get("cities") or read_cities():
        for sensor in read_sensors(city["cityName"]):
            try:
                forecast_result = fetch_forecast_result(city, sensor)
                (DATA_PROCESSED_PATH / city["cityName"] / sensor["sensorId"] / "predictions.json").write_text(
                    dumps(list(forecast_result.values()), indent=4, default=str))
            except Exception:
                logger.error(
                    f"Error occurred while fetching forecast values for {city['cityName']} - {sensor['sensorId']}",
                    exc_info=True)


@scheduler.scheduled_job(trigger="cron", id="reset_api_counter", misfire_grace_time=None, jobstore=jobstore_name,
                         hour=0)
def reset_api_counter() -> None:
    try:
        remove(DATA_PATH / f"{OPEN_WEATHER}.lock")
    except OSError:
        pass


@scheduler.scheduled_job(trigger="cron", id="reset_model_lock", misfire_grace_time=None, jobstore=jobstore_name,
                         month="*/2")
def reset_model_lock() -> None:
    for file in [Path(root) / file for root, _, files in walk(MODELS_PATH) for file in files if
                 file.endswith(".lock")]:
        last_modified = int(file.stat().st_mtime)
        if last_modified < int(datetime.timestamp(current_hour())) - 3600:
            remove(MODELS_PATH / file)


def configure_scheduler() -> None:
    db_url = f"sqlite:////{DATABASE_FILE}"
    engine = create_engine(db_url)
    jobstore = SQLAlchemyJobStore(engine=engine)
    scheduler.add_jobstore(jobstore=jobstore, alias=jobstore_name)
    scheduler.start()
    register(lambda: scheduler.shutdown(wait=False))
