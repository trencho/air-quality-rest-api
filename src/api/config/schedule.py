from base64 import b64encode
from datetime import datetime
from os import path, walk

from apscheduler.schedulers.background import BackgroundScheduler
from pandas import read_csv

from api.blueprints import current_hour, fetch_cities, fetch_city_data, fetch_sensors, next_hour, train_city_sensors
from api.config.git import append_commit_files, merge_csv_files, update_git_files
from definitions import pollutants, ROOT_DIR

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
        commit_message = 'Scheduled data dump - ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_git_files(file_names, file_list, repo_name, branch, commit_message)


@scheduler.scheduled_job(trigger='cron', minute=0)
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


@scheduler.scheduled_job(trigger='cron', day=1)
def model_training():
    cities = fetch_cities()
    for city in cities:
        sensors = fetch_sensors(city['cityName'])
        for sensor in sensors:
            for pollutant in pollutants:
                train_city_sensors(city, sensor, pollutant)


def schedule_jobs():
    scheduler.start()
