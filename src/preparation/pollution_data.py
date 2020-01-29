import base64

import numpy as np
import pandas as pd
import requests

from definitions import DATA_RAW_PATH

week_increment = 601200
timezone = '%2b02:00'

sensor_id = '1000'
value_types = ['pm10', 'pm25', 'temperature', 'humidity']

from_datetime = '2015-01-01T00:00:00%2b02:00'
from_timestamp = 1420070400
to_datetime = '2015-01-08T00:00:00%2b02:00'
to_timestamp = 1420675200

end_datetime = '2019-01-01T00:00:00%2b02:00'
end_timestamp = 1546304400

format_time = '%Y-%m-%dT%H:%M:%S%z'

df = pd.DataFrame()

pollution_data = DATA_RAW_PATH + '/pollution/pollution_report_Centar.csv'

from_test = '2017-03-15T02:00:00%2b01:00'
to_test = '2017-03-19T12:00:00%2b01:00'

get_url = 'https://skopje.pulse.eco/rest/dataRaw'
username = 'trencho'
password = 'test123'

while from_timestamp < end_timestamp:
    for value_type in value_types:
        get_parameters = {'sensorId': sensor_id, 'type': value_type, 'from': from_datetime, 'to': to_datetime}
        # get_parameters = {'sensorId': sensor_id, 'type': 'pm10', 'from': from_test, 'to': to_test}
        auth_str = '%s:%s' % (username, password)
        b64_auth_str = base64.b64encode(auth_str.encode())

        headers = {'Authorization': 'Basic %s' % b64_auth_str.decode()}

        pollution_request = requests.get(get_url, params=get_parameters, headers=headers)
        print(pollution_request.request.headers)
        pollution_json = pollution_request.json()
        # pollution_json = requests.get(get_url, params=get_parameters, auth=(username, password)).json()

        requests.get('https://skopje.pulse.eco/rest/dataRaw', json=get_parameters, headers=headers).text()

        df.append(pollution_json, ignore_index=True, sort=True)

        from_timestamp += week_increment
        from_datetime = pd.to_datetime(from_timestamp).isoformat()
        from_datetime = from_datetime.replace(from_datetime[19:], timezone)
        to_timestamp += week_increment
        to_datetime = pd.to_datetime(to_timestamp).isoformat()
        to_datetime = to_datetime.replace(to_datetime[19:], timezone)

        # df.stamp = pd.to_datetime(df.time).isoformat().astype(np.int64) // 10**9
        df.stamp = pd.to_datetime(df.time, format=format_time).astype(np.int64) // 10 ** 9
        df.sort_values(by='stamp')
        df.to_csv(pollution_data, index=False)
