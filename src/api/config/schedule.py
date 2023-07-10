from base64 import b64encode
from datetime import datetime
from json import dump, load
from os import environ, makedirs, path, remove, rmdir, walk
from shutil import unpack_archive

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
from flask_apscheduler import APScheduler

from api.blueprints import fetch_city_data
from definitions import COLLECTIONS, DATA_EXTERNAL_PATH, DATA_PATH, DATA_PROCESSED_PATH, DATA_RAW_PATH, MODELS_PATH, \
    POLLUTANTS, REPO_NAME
from modeling import train_regression_model
from preparation import fetch_cities, fetch_countries, fetch_sensors, read_cities, read_sensors
from processing import fetch_forecast_result, process_data, read_csv_in_chunks, save_dataframe
from .cache import cache
from .git import append_commit_files, create_archive, update_git_files
from .logger import logger
from .repository import RepositorySingleton

scheduler = APScheduler(scheduler=AsyncIOScheduler())
repository = RepositorySingleton.get_instance().get_repository()


@scheduler.task(trigger="cron", day="*/15")
async def dump_data() -> None:
    file_list, file_names = [], []
    for root, directories, files in walk(DATA_PATH):
        if not directories and files:
            file_path = f"{root}.zip"
            await create_archive(source=root, destination=file_path)
            with open(file_path, "rb") as in_file:
                data = b64encode(in_file.read())
            await append_commit_files(file_list, data, path.dirname(path.abspath(root)), path.basename(file_path),
                                      file_names)
            remove(file_path)

    if file_list:
        await update_git_files(file_list, file_names, environ[REPO_NAME], "master",
                               f"Scheduled data dump - {datetime.now().strftime('%H:%M:%S %d-%m-%Y')}")


@scheduler.task(trigger="cron", hour="*/2")
async def fetch_hourly_data() -> None:
    for city in cache.get("cities") or read_cities():
        for sensor in read_sensors(city["cityName"]):
            fetch_city_data(city["cityName"], sensor)
            for collection in COLLECTIONS:
                await process_data(city["cityName"], sensor["sensorId"], collection)


@scheduler.task(trigger="cron", hour=0)
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


@scheduler.task(trigger="cron", hour=0)
async def import_data() -> None:
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


@scheduler.task(trigger="cron", minute=0)
async def model_training() -> None:
    for file in [path.join(root, file) for root, directories, files in walk(MODELS_PATH) for file in files if
                 file.endswith(".lock")]:
        remove(path.join(MODELS_PATH, file))

    for city in cache.get("cities") or read_cities():
        for sensor in read_sensors(city["cityName"]):
            for pollutant in POLLUTANTS:
                await train_regression_model(city, sensor, pollutant)


@scheduler.task(trigger="cron", minute=0)
async def predict_locations() -> None:
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
                forecast_result = await fetch_forecast_result(city, sensor)
                with open(path.join(DATA_PROCESSED_PATH, city["cityName"], sensor["sensorId"], "predictions.json"),
                          "w") as out_file:
                    dump(list(forecast_result.values()), out_file, indent=4, default=str)
            except Exception:
                logger.error(
                    f"Error occurred while fetching forecast values for {city['cityName']} - {sensor['sensorId']}",
                    exc_info=True)


@scheduler.task(trigger="cron", hour=0)
async def reset_api_counter() -> None:
    try:
        remove(path.join(DATA_PATH, "onecall_counter.txt"))
        remove(path.join(DATA_PATH, "forecast_counter.txt"))
    except OSError:
        pass


def schedule_jobs(app: Flask) -> None:
    scheduler.api_enabled = True
    scheduler.init_app(app)
