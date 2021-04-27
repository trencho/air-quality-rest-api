from os import path

from pandas import merge as pandas_merge, read_csv

from preparation import save_dataframe


def merge_air_quality_data(data_path, city_name, sensor_id):
    try:
        weather_data = read_csv(path.join(data_path, city_name, sensor_id, 'weather.csv'))
        pollution_data = read_csv(path.join(data_path, city_name, sensor_id, 'pollution.csv'))
    except FileNotFoundError:
        return

    dataframe = pandas_merge(weather_data.drop_duplicates(), pollution_data.drop_duplicates(), on='time')

    if not dataframe.empty:
        data_path = path.join(data_path, city_name, sensor_id, 'summary.csv')
        save_dataframe(dataframe, 'summary', data_path, sensor_id)
