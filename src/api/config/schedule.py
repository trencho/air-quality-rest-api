import base64
from datetime import datetime
from os import path, walk

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

from api.config.git import append_commit_files, update_git_files
from api.resources import current_hour, fetch_cities, fetch_city_data, fetch_sensors, next_hour, train_city_sensors
from definitions import pollutants, ROOT_DIR


def data_dump():
    file_list = []
    file_names = []
    for root, directories, files in walk(ROOT_DIR):
        for file in files:
            if file.endswith('.csv'):
                data = pd.read_csv(path.join(root, file)).to_csv(index=False)
                append_commit_files(file_list, file_names, root, data, file)
            elif file.endswith('.png'):
                with open(path.join(root, file), 'rb') as input_file:
                    data = base64.b64encode(input_file.read())
                append_commit_files(file_list, file_names, root, data, file)

    if file_list:
        repo_name = 'air-quality-data-dump'
        branch = 'master'
        commit_message = 'Scheduled data dump - ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_git_files(file_names, file_list, repo_name, branch, commit_message)


def fetch_hourly_data():
    current_datetime = current_hour(datetime.now())
    current_timestamp = int(datetime.timestamp(current_datetime))
    start_time = current_timestamp

    next_hour_datetime = next_hour(current_datetime)
    next_hour_timestamp = int(datetime.timestamp(next_hour_datetime))
    end_time = next_hour_timestamp

    cities = fetch_cities()
    for city in cities:
        sensors = fetch_sensors(city['cityName'])
        for sensor in sensors:
            fetch_city_data(city['cityName'], sensor, start_time, end_time)


def model_training():
    cities = fetch_cities()
    for city in cities:
        sensors = fetch_sensors(city['cityName'])
        for sensor in sensors:
            for pollutant in pollutants:
                train_city_sensors(city, sensor, pollutant)


def schedule_operations():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=data_dump, trigger='cron', day=1)
    scheduler.add_job(func=fetch_hourly_data, trigger='cron', minute=0)
    scheduler.add_job(func=model_training, trigger='cron', day=1)

    scheduler.start()
