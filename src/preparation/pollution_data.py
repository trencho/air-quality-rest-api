import traceback
from datetime import datetime
from json import load as json_load
from os import environ

from numpy import int64
from pandas import DataFrame, json_normalize, to_datetime as pandas_to_datetime, to_numeric
from pytz import timezone
from requests import get as requests_get
from timezonefinder import TimezoneFinder

from definitions import DATA_EXTERNAL_PATH, pulse_eco_env_value, pollutants
from preparation import save_dataframe
from processing.normalize_data import normalize_pollution_data

hour_in_secs = 3600
week_in_seconds = 604800


def format_datetime(timestamp, tz):
    dt = datetime.fromtimestamp(timestamp)
    dt = tz.localize(dt)
    dt = dt.isoformat()
    dt = dt.replace('+', '%2b')
    return dt


def extract_pollution_json(city_name, sensor, start_timestamp, end_timestamp):
    url = 'https://' + city_name + '.pulse.eco/rest/dataRaw'

    pulse_eco_env = environ.get(pulse_eco_env_value)
    with open(pulse_eco_env) as pulse_eco_file:
        pulse_eco_json = json_load(pulse_eco_file)
    username = pulse_eco_json.get('username')
    password = pulse_eco_json.get('password')

    tf = TimezoneFinder()
    sensor_position = sensor['position'].split(',')
    latitude, longitude = float(sensor_position[0]), float(sensor_position[1])
    sensor_loc = tf.timezone_at(lng=longitude, lat=latitude)
    sensor_tz = timezone(sensor_loc)

    from_timestamp = start_timestamp
    from_datetime = format_datetime(from_timestamp, sensor_tz)

    to_timestamp = start_timestamp + week_in_seconds
    to_datetime = format_datetime(to_timestamp, sensor_tz)

    dataframe = DataFrame()
    while from_timestamp < end_timestamp:
        for pollutant in pollutants:
            parameters = 'sensorId=' + sensor['sensorId'] + '&' + 'type=' + pollutant + '&' + 'from=' + from_datetime \
                         + '&' + 'to=' + to_datetime
            with requests_get(url=url, params=parameters, auth=(username, password)) as pollution_response:
                try:
                    pollution_json = pollution_response.json()
                    dataframe = dataframe.append(json_normalize(pollution_json), ignore_index=True)
                except ValueError:
                    print(pollution_response)
                    print(traceback.format_exc())

        if not dataframe.empty:
            dataframe.sort_values(by='stamp', inplace=True)
            dataframe['stamp'] = pandas_to_datetime(dataframe['stamp'])
            last_datetime = dataframe['stamp'].iloc[-1]
            last_timestamp = datetime.timestamp(last_datetime)
            if from_timestamp < last_timestamp:
                from_timestamp = last_timestamp
                to_timestamp += week_in_seconds
            else:
                from_timestamp += hour_in_secs
                to_timestamp += hour_in_secs
            from_datetime = format_datetime(from_timestamp, sensor_tz)
            to_datetime = format_datetime(to_timestamp, sensor_tz)
        else:
            from_timestamp += hour_in_secs
            from_datetime = format_datetime(from_timestamp, sensor_tz)
            to_timestamp += hour_in_secs
            to_datetime = format_datetime(to_timestamp, sensor_tz)

    if not dataframe.empty:
        dataframe.rename(columns={'stamp': 'time'}, inplace=True)
        dataframe['time'] = pandas_to_datetime(dataframe['time'])
        dataframe['time'] = dataframe['time'].values.astype(int64) // 10 ** 9
        dataframe['value'] = to_numeric(dataframe['value'])
        dataframe.drop(columns='sensorId', inplace=True, errors='ignore')
        dataframe.sort_values(by='time', inplace=True)

        dataframe = normalize_pollution_data(dataframe)
        pollution_data_path = DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor['sensorId'] + '/pollution_report.csv'
        save_dataframe(dataframe, 'pollution', pollution_data_path, sensor['sensorId'])
