from base64 import b64encode
from datetime import datetime
from os import path, walk

from apscheduler.schedulers.background import BackgroundScheduler
from pandas import read_csv

from api.blueprints import fetch_city_data, train_city_sensors
from definitions import pollutants, ROOT_DIR
from preparation import fetch_cities, fetch_sensors
from processing import current_hour, next_hour
from .cache import cache
from .database import mongo
from .git import append_commit_files, merge_csv_files, update_git_files

scheduler = BackgroundScheduler()


@scheduler.scheduled_job(trigger='cron', day=1)
def data_dump():
    repo_name = 'air-quality-data-dump'

    file_list = []
    file_names = []
    for root, directories, files in walk(ROOT_DIR):
        for file in files:
            file_path = path.join(root, file)
            if file.endswith('.csv'):
                data = read_csv(file_path).to_csv(index=False)
                data = merge_csv_files(repo_name, file_path, data)
                append_commit_files(file_list, file_names, root, data, file)
            elif file.endswith('.png'):
                with open(file_path, 'rb') as input_file:
                    data = b64encode(input_file.read())
                append_commit_files(file_list, file_names, root, data, file)

    if file_list:
        branch = 'master'
        commit_message = f'Scheduled data dump - {datetime.now().strftime("%H:%M:%S %d-%m-%Y")}'
        update_git_files(file_names, file_list, repo_name, branch, commit_message)


@scheduler.scheduled_job(trigger='cron', minute=0)
def fetch_hourly_data():
    current_datetime = current_hour(datetime.now())
    current_timestamp = int(datetime.timestamp(current_datetime))
    start_time = current_timestamp

    next_hour_datetime = next_hour(current_datetime)
    next_hour_timestamp = int(datetime.timestamp(next_hour_datetime))
    end_time = next_hour_timestamp

    cities = cache.get('cities') or []
    for city in cities:
        sensors = cache.get('sensors') or {}
        for sensor in sensors[city['cityName']]:
            fetch_city_data(city['cityName'], sensor, start_time, end_time)


@scheduler.scheduled_job(trigger='cron', day=1)
def model_training():
    cities = cache.get('cities') or []
    for city in cities:
        sensors = cache.get('sensors') or {}
        for sensor in sensors[city['cityName']]:
            for pollutant in pollutants:
                train_city_sensors(city, sensor, pollutant)


@scheduler.scheduled_job(trigger='cron', hour=0)
def update_location_data():
    updated_cities = fetch_cities()
    cache.set('cities', updated_cities)
    updated_sensors = {}
    for city in updated_cities:
        mongo.db['cities'].replace_one({'cityName': city['cityName']}, city, upsert=True)
        updated_sensors[city['cityName']] = fetch_sensors(city['cityName'])
        for sensor in updated_sensors[city['cityName']]:
            sensor['cityName'] = city['cityName']
            mongo.db['sensors'].replace_one({'sensorId': sensor['sensorId']}, sensor, upsert=True)

    cache.set('sensors', updated_sensors)


def schedule_jobs():
    scheduler.start()
