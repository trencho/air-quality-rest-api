from os import environ, path
from pickle import dump, HIGHEST_PROTOCOL, load
from typing import Optional

from pandas import concat, DataFrame, read_csv, to_datetime

from api.config.database import mongo
from definitions import chunk_size, mongodb_connection


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
    chunks = []
    for chunk in read_csv(data_path, index_col=index_col, chunksize=chunk_size):
        chunk.index = to_datetime(chunk.index, unit="s")
        if len(chunk.index) > 0:
            chunks.append(chunk)

    return concat(chunks) if len(chunks) > 0 else None


def rename_features(dataframe: DataFrame) -> None:
    dataframe.rename(
        columns={"dt": "time", "temperature": "temp", "apparentTemperature": "feels_like", "dewPoint": "dew_point",
                 "cloudCover": "clouds", "windSpeed": "wind_speed", "windGust": "wind_gust", "windBearing": "wind_deg",
                 "summary": "weather.description", "icon": "weather.icon", "uvIndex": "uvi",
                 "precipIntensity": "precipitation", "AQI": "aqi", "CO": "co", "CO2": "co2", "NH3": "nh3", "NO": "no",
                 "NO2": "no2", "O3": "o3", "PM25": "pm2_5", "PM10": "pm10", "SO2": "so2"}, inplace=True,
        errors="ignore")


def save_dataframe(dataframe: DataFrame, collection: str, collection_path: str, sensor_id: str) -> None:
    rename_features(dataframe)
    drop_unnecessary_features(dataframe)

    if (mongodb_env := environ.get(mongodb_connection)) is not None:
        db_records = DataFrame(list(mongo.db[collection].find({"sensorId": sensor_id}, projection={"_id": False})))

        if len(db_records.index) > 0:
            dataframe = find_missing_data(dataframe, db_records, "time")

    trim_dataframe(dataframe, "time")
    if len(dataframe.index) > 0:
        dataframe.loc[:, "sensorId"] = sensor_id
        if mongodb_env is not None:
            mongo.db[collection].insert_many(dataframe.to_dict("records"))

        if (df := read_csv_in_chunks(collection_path)) is not None:
            dataframe = find_missing_data(dataframe, df, "time")
        dataframe.drop(columns="sensorId", inplace=True, errors="ignore")
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
