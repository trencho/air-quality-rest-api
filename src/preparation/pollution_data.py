import base64
import json

import numpy as np
import pandas as pd
import requests

from definitions import DATA_EXTERNAL_PATH
from definitions import pollutants


def extract_pollution_json(pulse_eco_env, city, sensor_id, start_time, end_time):
    url = 'https://' + city + '.pulse.eco/rest/dataRaw'
    pulse_eco_json = json.load(pulse_eco_env)
    username = pulse_eco_json.get('username')
    password = pulse_eco_json.get('password')

    week_increment = 604800
    timezone = '%2b02:00'

    from_datetime = '2015-01-01T00:00:00%2b02:00'
    from_timestamp = 1420070400
    to_datetime = '2015-01-08T00:00:00%2b02:00'
    to_timestamp = 1420675200

    end_datetime = '2019-01-01T00:00:00%2b02:00'
    end_timestamp = 1546304400

    format_time = '%Y-%m-%dT%H:%M:%S%z'

    df = pd.DataFrame()

    pollution_data = DATA_EXTERNAL_PATH + '/' + city + '/' + sensor_id + '/pollution_report.csv'

    # from_test = '2017-03-15T02:00:00%2b01:00'
    # to_test = '2017-03-19T12:00:00%2b01:00'

    while from_timestamp < end_timestamp:
        for pollutant in pollutants:
            parameters = {'sensorId': sensor_id, 'type': pollutant, 'from': from_datetime, 'to': to_datetime}
            auth_str = '%s:%s' % (username, password)
            b64_auth_str = base64.b64encode(auth_str)

            headers = {'Authorization': 'Basic %s' % b64_auth_str.decode()}

            pollution_request = requests.get(url, params=parameters, headers=headers)
            print(pollution_request.request.headers)
            pollution_json = requests.get(url, params=parameters, headers=headers).json()

            requests.get('https://' + city + '.pulse.eco/rest/dataRaw', json=parameters, headers=headers).text()

            df.append(pollution_json, ignore_index=True, sort=True)

            from_timestamp += week_increment
            from_datetime = pd.to_datetime(from_timestamp).isoformat()
            from_datetime = from_datetime.replace(from_datetime[19:], timezone)
            to_timestamp += week_increment
            to_datetime = pd.to_datetime(to_timestamp).isoformat()
            to_datetime = to_datetime.replace(to_datetime[19:], timezone)

            # df.stamp = pd.to_datetime(df.time).isoformat().astype(np.int64) // 10**9
            df['stamp'] = pd.to_datetime(df['time'], format=format_time).astype(np.int64) // 10 ** 9
            df.sort_values(by='stamp')
            df.to_csv(pollution_data, index=False)
