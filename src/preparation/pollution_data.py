import json
from datetime import datetime

import pandas as pd
import requests
from pytz import timezone
from timezonefinder import TimezoneFinder

from definitions import DATA_EXTERNAL_PATH
from definitions import pollutants

week_increment = 604800
time_format = '%Y-%m-%d %H:%M:%S%z'
custom_time_format = '%Y-%m-%dT%H:%M:%S%z'


def format_datetime(timestamp, tz):
    dt = datetime.fromtimestamp(timestamp)
    dt = tz.localize(dt)
    dt = dt.strftime(custom_time_format)
    dt = dt.replace("+", "%2")
    dt = dt[:25] + ':' + dt[25:]
    return dt


def replace_last_occurrence(s, old, new):
    li = s.rsplit(old, 1)  # Split only once
    return new.join(li)


def extract_pollution_json(pulse_eco_env, city, sensor, start_timestamp, end_timestamp):
    url = 'https://' + city + '.pulse.eco/rest/dataRaw'
    pulse_eco_json = json.load(pulse_eco_env)
    username = pulse_eco_json.get('username')
    password = pulse_eco_json.get('password')
    # session = requests.Session()
    # session.auth = (username, password)

    tf = TimezoneFinder()
    sensor_position = sensor['position'].split(',')
    latitude, longitude = float(sensor_position[0]), float(sensor_position[1])
    sensor_loc = tf.timezone_at(lng=longitude, lat=latitude)
    sensor_tz = timezone(sensor_loc)

    from_timestamp = start_timestamp
    from_datetime = format_datetime(from_timestamp, sensor_tz)

    to_timestamp = start_timestamp + week_increment
    to_datetime = format_datetime(to_timestamp, sensor_tz)

    df = pd.DataFrame()
    while from_timestamp < end_timestamp:
        for pollutant in pollutants:
            parameters = {'sensorId': sensor['sensor_id'], 'type': pollutant, 'from': from_datetime, 'to': to_datetime}
            with requests.Session() as session:
                session.auth = (username, password)
                pollution_response = session.get(url=url, params=parameters)
                try:
                    pollution_json = pollution_response.json()
                    df.append(pollution_json, ignore_index=True, sort=True)
                except ValueError:
                    print('Response did not return JSON')
            # pollution_json = session.get(url, params=parameters).json()

        from_timestamp += week_increment
        from_datetime = format_datetime(from_timestamp, sensor_tz)
        to_timestamp += week_increment
        to_datetime = format_datetime(to_timestamp, sensor_tz)

    df.rename(columns={'stamp': 'time'}, inplace=True)
    df['time'] = df['time'].replace('T', ' ')
    df['time'] = df['time'].apply(lambda x: replace_last_occurrence(x, ':', ''), axis=1)
    df['time'] = datetime.strptime(df['time'], time_format)
    df['time'] = datetime.timestamp(df['time'])
    df.sort_values(by='time')

    pollution_data = DATA_EXTERNAL_PATH + '/' + city + '/' + sensor['sensor_id'] + '/pollution_report.csv'
    df.to_csv(pollution_data, index=False)
