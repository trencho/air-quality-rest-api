from datetime import datetime
from os import environ, path
from traceback import format_exc

from numpy import int64
from pandas import DataFrame, json_normalize, to_datetime as pandas_to_datetime, to_numeric
from pytz import timezone
from requests import get as requests_get
from timezonefinder import TimezoneFinder

from definitions import DATA_EXTERNAL_PATH, pulse_eco_user_name_env_value, pulse_eco_user_pass_env_value, pollutants, \
    hour_in_secs
from processing.normalize_data import normalize_pollution_data
from .handle_data import save_dataframe

week_in_seconds = 604800


def format_datetime(timestamp, tz):
    dt = datetime.fromtimestamp(timestamp)
    dt = tz.localize(dt)
    dt = dt.isoformat()
    dt = dt.replace('+', '%2b')
    return dt


def fetch_pollution_data(city_name, sensor, start_time, end_time):
    url = f'https://{city_name}.pulse.eco/rest/dataRaw'

    username = environ[pulse_eco_user_name_env_value]
    password = environ[pulse_eco_user_pass_env_value]

    tf = TimezoneFinder()
    sensor_position = sensor['position'].split(',')
    latitude, longitude = float(sensor_position[0]), float(sensor_position[1])
    sensor_loc = tf.timezone_at(lng=longitude, lat=latitude)
    sensor_tz = timezone(sensor_loc)

    from_timestamp = start_time
    from_datetime = format_datetime(from_timestamp, sensor_tz)

    to_timestamp = start_time + week_in_seconds
    to_datetime = format_datetime(to_timestamp, sensor_tz)

    dataframe = DataFrame()
    while from_timestamp < end_time:
        for pollutant in pollutants:
            parameters = f'sensorId={sensor["sensorId"]}&type={pollutant}&from={from_datetime}&to={to_datetime}'
            pollution_response = requests_get(url=url, params=parameters, auth=(username, password))
            try:
                pollution_json = pollution_response.json()
                dataframe = dataframe.append(json_normalize(pollution_json), ignore_index=True)
            except ValueError:
                print(pollution_response)
                print(format_exc())

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

    dataframe.rename(columns={'stamp': 'time'}, inplace=True, errors='ignore')
    dataframe['time'] = pandas_to_datetime(dataframe['time'], errors='ignore')

    dataframe['value'] = to_numeric(dataframe['value'], errors='ignore')
    dataframe.drop(columns='sensorId', inplace=True, errors='ignore')

    if not dataframe.empty:
        dataframe['time'] = dataframe['time'].values.astype(int64) // 10 ** 9
        dataframe.drop(index=dataframe.loc[dataframe['time'] > end_time].index, inplace=True, errors='ignore')
        dataframe = normalize_pollution_data(dataframe)
        pollution_data_path = path.join(DATA_EXTERNAL_PATH, city_name, sensor['sensorId'], 'pollution.csv')
        save_dataframe(dataframe, 'pollution', pollution_data_path, sensor['sensorId'])
