from base64 import b64encode
from datetime import datetime
from os import path, walk

from apscheduler.schedulers.background import BackgroundScheduler
from pandas import read_csv

from api.blueprints import current_hour, fetch_city_data, next_hour, train_city_sensors
from definitions import pollutants, ROOT_DIR
from preparation import fetch_cities, fetch_sensors
from preparation.location_data import cities, sensors
from .db import mongo
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

    for city in cities:
        for sensor in sensors[city['cityName']]:
            fetch_city_data(city['cityName'], sensor, start_time, end_time)


@scheduler.scheduled_job(trigger='cron', day=1)
def model_training():
    for city in cities:
        for sensor in sensors[city['cityName']]:
            for pollutant in pollutants:
                train_city_sensors(city, sensor, pollutant)


@scheduler.scheduled_job(trigger='cron', hour=0)
def update_location_data():
    cities = fetch_cities()
    for city in cities:
        mongo.db['cities'].replace_one({'cityName': city['cityName']}, city, upsert=True)
        sensors[city['cityName']] = fetch_sensors(city['cityName'])
        for sensor in sensors[city['cityName']]:
            sensor['cityName'] = city['cityName']
            mongo.db['sensors'].replace_one({'sensorId': sensor['sensorId']}, sensor, upsert=True)


def schedule_jobs():
    scheduler.start()
