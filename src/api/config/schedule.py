from base64 import b64encode
from datetime import datetime
from json import dump
from os import environ, makedirs, path, remove, walk
from shutil import make_archive, rmtree

from apscheduler.schedulers.background import BackgroundScheduler
from pandas import read_csv

from api.blueprints import fetch_city_data
from definitions import DATA_EXTERNAL_PATH, DATA_PATH, DATA_RAW_PATH, MODELS_PATH, mongodb_connection, pollutants, \
    repo_name, ROOT_PATH
from modeling import train_regression_model
from preparation import fetch_cities, fetch_sensors, read_cities, read_sensors, save_dataframe
from processing import merge_air_quality_data
from processing.forecast_data import fetch_forecast_result
from .cache import cache
from .database import mongo
from .git import append_commit_files, update_git_files

scheduler = BackgroundScheduler()


@scheduler.scheduled_job(trigger='cron', day=1)
def data_dump() -> None:
    make_archive(DATA_PATH, 'zip', DATA_PATH)

    file_list, file_names = [], []
    for root, directories, files in walk(ROOT_PATH):
        for file in files:
            if file.endswith('.zip'):
                with open(path.join(root, file), 'rb') as in_file:
                    data = b64encode(in_file.read())
                append_commit_files(file_list, data, root, file, file_names)
                remove(path.join(root, file))

    if file_list:
        branch = 'master'
        commit_message = f'Scheduled data dump - {datetime.now().strftime("%H:%M:%S %d-%m-%Y")}'
        update_git_files(file_list, file_names, environ[repo_name], branch, commit_message)


@scheduler.scheduled_job(trigger='cron', hour='*/2')
def fetch_hourly_data() -> None:
    for city in cache.get('cities') or read_cities():
        for sensor in read_sensors(city['cityName']):
            fetch_city_data(city['cityName'], sensor)


@scheduler.scheduled_job(trigger='cron', hour=0)
def fetch_locations() -> None:
    cities = fetch_cities()
    with open(path.join(DATA_RAW_PATH, 'cities.json'), 'w') as out_file:
        dump(cities, out_file, indent=4)
    cache.set('cities', cities)
    sensors = {}
    for city in cities:
        if (mongodb_env := environ.get(mongodb_connection)) is not None:
            mongo.db['cities'].replace_one({'cityName': city['cityName']}, city, upsert=True)
        sensors[city['cityName']] = fetch_sensors(city['cityName'])
        for sensor in sensors[city['cityName']]:
            sensor['cityName'] = city['cityName']
            if mongodb_env is not None:
                mongo.db['sensors'].replace_one({'sensorId': sensor['sensorId']}, sensor, upsert=True)
        makedirs(path.join(DATA_RAW_PATH, city['cityName']), exist_ok=True)
        with open(path.join(DATA_RAW_PATH, city['cityName'], 'sensors.json'), 'w') as out_file:
            dump(sensors[city['cityName']], out_file, indent=4)


@scheduler.scheduled_job(trigger='cron', hour=0)
def import_data() -> None:
    for root, directories, files in walk(DATA_EXTERNAL_PATH):
        for file in files:
            file_path = path.join(root, file)
            if file.endswith('weather.csv') or file.endswith('pollution.csv'):
                dataframe = read_csv(file_path)
                save_dataframe(dataframe, path.splitext(file)[0], None, path.basename(path.dirname(file_path)))

    for city in cache.get('cities') or read_cities():
        for sensor in read_sensors(city['cityName']):
            merge_air_quality_data(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId'])
            rmtree(path.join(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId']), ignore_errors=True)


@scheduler.scheduled_job(trigger='cron', day=1)
def model_training() -> None:
    for file in [path.join(root, file) for root, directories, files in walk(MODELS_PATH) for file in files if
                 file.endswith('.lock')]:
        remove(path.join(MODELS_PATH, file))

    for city in cache.get('cities') or read_cities():
        for sensor in read_sensors(city['cityName']):
            for pollutant in pollutants:
                train_regression_model(city, sensor, pollutant)


@scheduler.scheduled_job(trigger='cron', minute=0)
def predict_locations() -> None:
    if environ.get(mongodb_connection) is not None:
        for city in cache.get('cities') or read_cities():
            for sensor in read_sensors(city['cityName']):
                mongo.db['predictions'].replace_one({'cityName': city['cityName'], 'sensorId': sensor['sensorId']}, {
                    'data': [*fetch_forecast_result(city, sensor, daemon=False).values()], 'cityName': city['cityName'],
                    'sensorId': sensor['sensorId']}, upsert=True)


def schedule_jobs() -> None:
    scheduler.start()
