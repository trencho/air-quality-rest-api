from base64 import b64encode
from datetime import datetime
from json import dump as json_dump
from os import environ, makedirs, path, rmdir, walk

from apscheduler.schedulers.background import BackgroundScheduler
from flask_pymongo import ASCENDING
from pandas import read_csv

from api.blueprints import fetch_city_data
from definitions import DATA_EXTERNAL_PATH, DATA_RAW_PATH, mongodb_connection, pollutants, repo_name, ROOT_PATH
from modeling import train_city_sensors
from preparation import fetch_cities, fetch_sensors, save_dataframe
from processing import merge_air_quality_data
from .cache import cache
from .database import mongo
from .git import append_commit_files, merge_csv_files, update_git_files

scheduler = BackgroundScheduler()


@scheduler.scheduled_job(trigger='cron', day=1)
def data_dump():
    repository_name = environ[repo_name]

    file_list = []
    file_names = []
    for root, directories, files in walk(ROOT_PATH):
        for file in files:
            file_path = path.join(root, file)
            if file.endswith('.csv'):
                data = read_csv(file_path).to_csv(index=False)
                data = merge_csv_files(repository_name, file_path, data)
                append_commit_files(file_list, file_names, root, data, file)
            elif file.endswith('.png'):
                with open(file_path, 'rb') as in_file:
                    data = b64encode(in_file.read())
                append_commit_files(file_list, file_names, root, data, file)

    if file_list:
        branch = 'master'
        commit_message = f'Scheduled data dump - {datetime.now().strftime("%H:%M:%S %d-%m-%Y")}'
        update_git_files(file_names, file_list, repository_name, branch, commit_message)


@scheduler.scheduled_job(trigger='cron', hour='*/2')
def fetch_hourly_data():
    cities = cache.get('cities') or []
    for city in cities:
        sensors = cache.get('sensors') or {}
        for sensor in sensors[city['cityName']]:
            fetch_city_data(city['cityName'], sensor)


@scheduler.scheduled_job(trigger='cron', hour=0)
def import_data():
    for root, directories, files in walk(DATA_EXTERNAL_PATH):
        for file in files:
            file_path = path.join(root, file)
            if file.endswith('weather.csv') or file.endswith('pollution.csv'):
                dataframe = read_csv(file_path)
                save_dataframe(dataframe, path.splitext(file)[0], None, path.basename(path.dirname(file_path)))

    cities = cache.get('cities') or []
    for city in cities:
        sensors = cache.get('sensors') or {}
        for sensor in sensors[city['cityName']]:
            merge_air_quality_data(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId'])
            rmdir(path.join(DATA_EXTERNAL_PATH, city['cityName'], sensor['sensorId']))


@scheduler.scheduled_job(trigger='cron', day=1)
def model_training():
    cities = cache.get('cities') or []
    for city in cities:
        sensors = cache.get('sensors') or {}
        for sensor in sensors[city['cityName']]:
            for pollutant in pollutants:
                train_city_sensors(city, sensor, pollutant)


@scheduler.scheduled_job(trigger='cron', hour=0)
def fetch_locations():
    if environ.get(mongodb_connection) is not None:
        mongo.db['cities'].create_index([('cityName', ASCENDING)])
        mongo.db['sensors'].create_index([('sensorId', ASCENDING)])

    cities = fetch_cities()
    with open(path.join(DATA_RAW_PATH, 'cities.json'), 'w') as out_file:
        json_dump(cities, out_file)
    cache.set('cities', cities)
    sensors = {}
    for city in cities:
        if environ.get(mongodb_connection) is not None:
            mongo.db['cities'].replace_one({'cityName': city['cityName']}, city, upsert=True)
        sensors[city['cityName']] = fetch_sensors(city['cityName'])
        for sensor in sensors[city['cityName']]:
            sensor['cityName'] = city['cityName']
            if environ.get(mongodb_connection) is not None:
                mongo.db['sensors'].replace_one({'sensorId': sensor['sensorId']}, sensor, upsert=True)
        makedirs(path.join(DATA_RAW_PATH, city['cityName']), exist_ok=True)
        with open(path.join(DATA_RAW_PATH, city['cityName'], 'sensors.json'), 'w') as out_file:
            json_dump(sensors[city['cityName']], out_file)

    cache.set('sensors', sensors)


def schedule_jobs():
    scheduler.start()
