from os import path

from pandas import merge

from api.config.logger import log
from .handle_data import read_csv_in_chunks, save_dataframe


def merge_air_quality_data(data_path: str, city_name: str, sensor_id: str) -> None:
    try:
        weather_data = read_csv_in_chunks(path.join(data_path, city_name, sensor_id, 'weather.csv'))
        pollution_data = read_csv_in_chunks(path.join(data_path, city_name, sensor_id, 'pollution.csv'))

        dataframe = merge(weather_data, pollution_data, on='time')

        if len(dataframe.index) > 0:
            save_dataframe(dataframe, 'summary', path.join(data_path, city_name, sensor_id, 'summary.csv'), sensor_id)
    except Exception:
        log.error(f'Error occurred while merging air quality data for {city_name} - {sensor_id}', exc_info=1)
