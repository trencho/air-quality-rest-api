from atexit import register
from base64 import b64encode
from datetime import datetime
from json import dump, load
from logging import getLogger
from os import environ, makedirs, path, remove, rmdir, walk
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
DATABASE_FILE = path.join(DATA_PATH, "jobs.sqlite")
REPO_BRANCH = "master"

repository = RepositorySingleton.get_instance().get_repository()


@scheduler.scheduled_job(trigger="cron", id="dump_data", misfire_grace_time=None, jobstore=jobstore_name, day="*/15")
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
        update_git_files(file_list, file_names, environ[REPO_NAME], REPO_BRANCH,
                         f"Scheduled data dump - {datetime.now().strftime('%H:%M:%S %d-%m-%Y')}")


@scheduler.scheduled_job(trigger="cron", id="dump_jobs", misfire_grace_time=None, jobstore=jobstore_name, hour=0)
def dump_jobs() -> None:
    dump_filename = "job_dump.sql"
    dump_content = generate_sql_dump(DATABASE_FILE)

    dump_path = path.join(DATA_PATH, dump_filename)
    with open(dump_path, 'w') as f:
        f.write(dump_content)


@scheduler.scheduled_job(trigger="cron", id="fetch_hourly_data", misfire_grace_time=None, jobstore=jobstore_name,
                         hour="*/2")
def fetch_hourly_data() -> None:
    if check_api_lock() is False:
        return
    for city in cache.get("cities") or read_cities():
        for sensor in read_sensors(city["cityName"]):
            fetch_city_data(city["cityName"], sensor)
            for collection in COLLECTIONS:
                if path.exists(path.join(DATA_RAW_PATH, city["cityName"], sensor["sensorId"], f"{collection}.csv")):
                    process_data(city["cityName"], sensor["sensorId"], collection)


@scheduler.scheduled_job(trigger="cron", id="fetch_locations", misfire_grace_time=None, jobstore=jobstore_name, hour=0)
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


@scheduler.scheduled_job(trigger="cron", id="import_data", misfire_grace_time=None, jobstore=jobstore_name, hour=0)
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


@scheduler.scheduled_job(trigger="cron", id="model_training", misfire_grace_time=None, max_instances=2,
                         jobstore=jobstore_name, minute=0)
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


@scheduler.scheduled_job(trigger="cron", id="reset_api_counter", misfire_grace_time=None, jobstore=jobstore_name,
                         hour=0)
def reset_api_counter() -> None:
    try:
        remove(path.join(DATA_PATH, f"{OPEN_WEATHER}.lock"))
    except OSError:
        pass


@scheduler.scheduled_job(trigger="cron", id="reset_model_lock", misfire_grace_time=None, jobstore=jobstore_name,
                         month="*/2")
def reset_model_lock() -> None:
    for file in [path.join(root, file) for root, directories, files in walk(MODELS_PATH) for file in files if
                 file.endswith(".lock")]:
        last_modified = int(path.getmtime(file))
        if last_modified < int(datetime.timestamp(current_hour())) - 3600:
            remove(path.join(MODELS_PATH, file))


def configure_scheduler() -> None:
    db_url = f"sqlite:////{DATABASE_FILE}"
    engine = create_engine(db_url)
    jobstore = SQLAlchemyJobStore(engine=engine)
    scheduler.add_jobstore(jobstore=jobstore, alias=jobstore_name)
    scheduler.start()
    register(lambda: scheduler.shutdown(wait=False))
