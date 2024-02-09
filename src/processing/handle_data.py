from logging import getLogger
from os import path
from pickle import dump, HIGHEST_PROTOCOL, load
from typing import Optional

from pandas import concat, DataFrame, read_csv, to_datetime

from api.config.repository import RepositorySingleton
from definitions import CHUNK_SIZE, COLLECTIONS

logger = getLogger(__name__)
repository = RepositorySingleton.get_instance().get_repository()


def convert_dtype(x: object) -> str:
    if not x:
        return ""
    try:
        return str(x)
    except Exception:
        return ""


def drop_unnecessary_features(dataframe: DataFrame) -> None:
    dataframe.drop(columns=dataframe.filter(regex="weather").columns, axis=1, inplace=True, errors="ignore")
    dataframe.drop(columns=["precipProbability", "precipType", "ozone", "co2"], inplace=True, errors="ignore")


def find_dtypes(file_path: str, collection: str) -> Optional[dict]:
    dtypes_path = path.join(file_path, f"{collection}_dtypes.pkl")
    if path.exists(dtypes_path):
        with open(dtypes_path, "rb") as in_file:
            return load(in_file)

    return None


def find_missing_data(new_dataframe: DataFrame, old_dataframe: DataFrame, column: str) -> DataFrame:
    dataframe = new_dataframe.loc[~new_dataframe[column].isin(old_dataframe[column])].copy()
    return dataframe[dataframe.columns.intersection(old_dataframe.columns.values.tolist())]


def read_csv_in_chunks(data_path: str, index_col: str = None) -> Optional[DataFrame]:
    chunks = [chunk for chunk in read_csv(data_path, index_col=index_col, chunksize=CHUNK_SIZE) if len(chunk.index) > 0]
    dataframe = concat(chunks)
    dataframe.index = to_datetime(dataframe.index, errors="coerce", unit="s")
    dataframe.drop_duplicates(keep="last", inplace=True)
    return dataframe.sort_index() if len(dataframe.index) > 0 else None


def rename_features(dataframe: DataFrame) -> None:
    dataframe.rename(
        columns={"dt": "time", "temperature": "temp", "apparentTemperature": "feels_like", "dewPoint": "dew_point",
                 "cloudCover": "clouds", "windSpeed": "wind_speed", "windGust": "wind_gust", "windBearing": "wind_deg",
                 "summary": "weather.description", "icon": "weather.icon", "uvIndex": "uvi",
                 "precipIntensity": "precipitation", "AQI": "aqi", "CO": "co", "CO2": "co2", "NH3": "nh3", "NO": "no",
                 "NO2": "no2", "O3": "o3", "PM25": "pm2_5", "PM10": "pm10", "SO2": "so2"}, inplace=True,
        errors="ignore")


def fetch_summary_dataframe(data_path: str, index_col: str) -> DataFrame:
    dataframe_list = [read_csv_in_chunks(path.join(data_path, f"{collection}.csv"), index_col=index_col) for collection
                      in COLLECTIONS]
    return concat(dataframe_list, axis=1, join="inner")


def save_dataframe(dataframe: DataFrame, collection: str, collection_path: str, sensor_id: str) -> None:
    rename_features(dataframe)
    drop_unnecessary_features(dataframe)

    db_records = DataFrame(
        repository.get_many(collection_name=collection, filter={"sensorId": sensor_id}, projection={"_id": False}))
    if len(db_records.index) > 0:
        dataframe = find_missing_data(dataframe, db_records, "time")

    trim_dataframe(dataframe, "time")
    if len(dataframe.index) == 0:
        return

    dataframe.loc[:, "sensorId"] = sensor_id
    repository.save_many(collection_name=collection, items=dataframe.to_dict("records"))

    try:
        df = read_csv_in_chunks(collection_path)
        dataframe = find_missing_data(dataframe, df, "time")
    except Exception:
        logger.error(f"Could not fetch data from local storage for {sensor_id} - {collection}", exc_info=True)
    dataframe.drop(columns="sensorId", inplace=True, errors="ignore")
    # TODO: Review this line for converting column data types
    # dataframe = dataframe.astype(column_dtypes, errors="ignore")
    dataframe.to_csv(collection_path, header=not path.exists(collection_path), index=False, mode="a")


def store_dtypes(file_path: str, collection: str, dtypes: dict) -> None:
    with open(path.join(file_path, f"{collection}_dtypes.pkl"), "wb") as out_file:
        dump(dtypes, out_file, HIGHEST_PROTOCOL)


def trim_dataframe(dataframe: DataFrame, column: str) -> None:
    dataframe.sort_values(by=column, inplace=True)
    dataframe.dropna(axis="columns", how="all", inplace=True)
    dataframe.dropna(axis="index", how="all", inplace=True)
    dataframe.drop_duplicates(subset=column, keep="last", inplace=True)
    dataframe.reset_index(drop=True, inplace=True)
