from json import dumps, loads
from logging import getLogger
from pathlib import Path
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


def drop_unnecessary_features(dataframe: DataFrame) -> DataFrame:
    dataframe = dataframe.drop(
        columns=dataframe.filter(regex="weather").columns, axis=1, errors="ignore"
    )
    dataframe = dataframe.drop(
        columns=["precipProbability", "precipType", "ozone", "co2"], errors="ignore"
    )
    return dataframe


def find_dtypes(file_path: Path, collection: str) -> Optional[dict]:
    dtypes_path = file_path / f"{collection}_dtypes.json"
    if dtypes_path.exists():
        return loads(dtypes_path.read_text())
    return None


def find_missing_data(
    new_dataframe: DataFrame, old_dataframe: DataFrame, column: str
) -> DataFrame:
    dataframe = new_dataframe.loc[
        ~new_dataframe[column].isin(old_dataframe[column])
    ].copy()
    return dataframe[
        dataframe.columns.intersection(old_dataframe.columns.values.tolist())
    ]


def read_csv_in_chunks(data_path: Path, index_col: str = None) -> Optional[DataFrame]:
    chunks = [
        chunk
        for chunk in read_csv(data_path, index_col=index_col, chunksize=CHUNK_SIZE)
        if len(chunk.index) > 0
    ]
    dataframe = concat(chunks)
    dataframe.index = to_datetime(dataframe.index, errors="coerce", unit="s")
    dataframe = dataframe.drop_duplicates(keep="last")
    return dataframe.sort_index() if len(dataframe.index) > 0 else None


def rename_features(dataframe: DataFrame) -> DataFrame:
    return dataframe.rename(
        columns={
            "dt": "time",
            "temperature": "temp",
            "apparentTemperature": "feels_like",
            "dewPoint": "dew_point",
            "cloudCover": "clouds",
            "windSpeed": "wind_speed",
            "windGust": "wind_gust",
            "windBearing": "wind_deg",
            "summary": "weather.description",
            "icon": "weather.icon",
            "uvIndex": "uvi",
            "precipIntensity": "precipitation",
            "AQI": "aqi",
            "CO": "co",
            "CO2": "co2",
            "NH3": "nh3",
            "NO": "no",
            "NO2": "no2",
            "O3": "o3",
            "PM25": "pm2_5",
            "PM10": "pm10",
            "SO2": "so2",
        },
        errors="ignore",
    )


def fetch_summary_dataframe(data_path: Path, index_col: str) -> DataFrame:
    dataframe_list = [
        read_csv_in_chunks(data_path / f"{collection}.csv", index_col=index_col)
        for collection in COLLECTIONS
    ]
    return concat(dataframe_list, axis=1, join="inner")


def save_dataframe(
    dataframe: DataFrame, collection: str, collection_path: Path, sensor_id: str
) -> None:
    dataframe = rename_features(dataframe)
    dataframe = drop_unnecessary_features(dataframe)

    db_records = DataFrame(
        repository.get_many(
            collection_name=collection,
            filter={"sensorId": sensor_id},
            projection={"_id": False},
        )
    )
    if len(db_records.index) > 0:
        dataframe = find_missing_data(dataframe, db_records, "time")

    dataframe = trim_dataframe(dataframe, "time")
    if len(dataframe.index) == 0:
        return

    dataframe.loc[:, "sensorId"] = sensor_id
    repository.save_many(collection_name=collection, items=dataframe.to_dict("records"))

    try:
        df = read_csv_in_chunks(collection_path)
        dataframe = find_missing_data(dataframe, df, "time")
    except Exception:
        logger.exception(
            f"Could not fetch data from local storage for {sensor_id} - {collection}",
        )
    dataframe = dataframe.drop(columns="sensorId", errors="ignore")
    # TODO: Review this line for converting column data types
    # dataframe = dataframe.astype(column_dtypes, errors="ignore")
    dataframe.to_csv(
        collection_path, header=not collection_path.exists(), index=False, mode="a"
    )


def store_dtypes(file_path: Path, collection: str, dtypes: dict) -> None:
    (file_path / f"{collection}_dtypes.json").write_text(dumps(dtypes, indent=4))


def trim_dataframe(dataframe: DataFrame, column: str) -> DataFrame:
    dataframe = dataframe.sort_values(by=column)
    dataframe = dataframe.dropna(axis="columns", how="all")
    dataframe = dataframe.dropna(axis="index", how="all")
    dataframe = dataframe.drop_duplicates(subset=column, keep="last")
    dataframe = dataframe.reset_index(drop=True)
    return dataframe
