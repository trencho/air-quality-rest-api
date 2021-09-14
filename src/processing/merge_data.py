from os import path

from pandas import merge, read_csv

from preparation import save_dataframe


def merge_air_quality_data(data_path: str, city_name: str, sensor_id: str) -> None:
    try:
        weather_data = read_csv(path.join(data_path, city_name, sensor_id, 'weather.csv'))
        pollution_data = read_csv(path.join(data_path, city_name, sensor_id, 'pollution.csv'))
    except FileNotFoundError:
        return

    dataframe = merge(weather_data.drop_duplicates(), pollution_data.drop_duplicates(), on='time')

    if not dataframe.empty:
        data_path = path.join(data_path, city_name, sensor_id, 'summary.csv')
        save_dataframe(dataframe, 'summary', data_path, sensor_id)
