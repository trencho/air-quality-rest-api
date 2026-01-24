from datetime import datetime, timedelta
from json import loads
from math import isnan, nan
from typing import Optional

from pandas import concat, DataFrame, date_range, Series

from api.config.cache import cache
from definitions import CACHE_TIMEOUTS, DATA_PROCESSED_PATH, MODELS_PATH, POLLUTANTS
from models import make_model
from models.base_regression_model import BaseRegressionModel
from preparation import location_timezone
from .feature_generation import encode_categorical_data, generate_features
from .feature_scaling import value_scaling
from .handle_data import fetch_summary_dataframe, read_csv_in_chunks
from .normalize_data import current_hour, next_hour

FORECAST_PERIOD = "1h"
FORECAST_STEPS = 25


def fetch_forecast_result(city: dict, sensor: dict) -> dict:
    forecast_result = {}
    for pollutant in POLLUTANTS:
        if (
            predictions := forecast_city_sensor(
                city["cityName"], sensor["sensorId"], pollutant
            )
        ) is None:
            continue

        for index, value in predictions.items():
            timestamp = int(index.timestamp())
            timestamp_dict = forecast_result.get(timestamp, {})
            date_time = datetime.fromtimestamp(
                timestamp, location_timezone(city["countryCode"])
            )
            timestamp_dict.update(
                {
                    "dateTime": date_time,
                    "time": timestamp,
                    pollutant: None if isnan(value) else value,
                }
            )
            forecast_result.update({timestamp: timestamp_dict})

    return forecast_result


@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
def forecast_city_sensor(
    city_name: str, sensor_id: str, pollutant: str
) -> Optional[Series]:
    if (load_model := load_regression_model(city_name, sensor_id, pollutant)) is None:
        return None

    model, model_features = load_model
    return recursive_forecast(city_name, sensor_id, pollutant, model, model_features)


@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
def forecast_sensor(city_name: str, sensor_id: str, timestamp: int) -> dict:
    dataframe = read_csv_in_chunks(
        DATA_PROCESSED_PATH / city_name / sensor_id / "weather.csv"
    )
    dataframe = dataframe.loc[dataframe["time"] == timestamp]
    if len(dataframe.index) > 0:
        return dataframe.to_dict("records")[0]

    return {}


@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
def load_regression_model(
    city_name: str, sensor_id: str, pollutant: str
) -> Optional[tuple]:
    model_dir = MODELS_PATH / city_name / sensor_id / pollutant

    files = list(model_dir.glob("*.mdl"))
    if not files:
        return None

    model_name = files[0].stem
    model = make_model(model_name)

    model.load(model_dir)
    model_features = loads((model_dir / "selected_features.json").read_text())

    return model, model_features


@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
def direct_forecast(
    y: Series,
    model: BaseRegressionModel,
    lags: int = FORECAST_STEPS,
    n_steps: int = FORECAST_STEPS,
    step: str = FORECAST_PERIOD,
) -> Series:
    """Multistep direct forecasting using a machine learning model to forecast each time period ahead

    Parameters
    ----------
    y: pd.Series holding the input time-series to forecast
    model: A model for iterative training
    lags: List of lags used for training the model
    n_steps: Number of time periods in the forecasting horizon
    step: The period of forecasting

    Returns
    -------
    forecast_values: pd.Series with forecasted values indexed by forecast horizon dates
    """

    def one_step_features(date, step: int):
        tmp = y[y.index <= date]
        features = generate_features(tmp, lags)
        target = y[y.index >= features.index[0] + timedelta(hours=step)]
        assert len(features.index) == len(target.index)
        return features, target

    forecast_values = []
    forecast_range = date_range(
        y.index[-1] + timedelta(hours=1), periods=n_steps, freq=step
    )
    forecast_features, _ = one_step_features(y.index[-1], 0)

    for s in range(1, n_steps + 1):
        last_date = y.index[-1] - timedelta(hours=s)
        features, target = one_step_features(last_date, s)
        model.train(features, target)
        predictions = model.predict(forecast_features)
        forecast_values.append(predictions[-1])

    return Series(forecast_values, forecast_range)


@cache.memoize(timeout=CACHE_TIMEOUTS["1h"])
def recursive_forecast(
    city_name: str,
    sensor_id: str,
    pollutant: str,
    model: BaseRegressionModel,
    model_features: list,
    lags: int = FORECAST_STEPS,
    n_steps: int = FORECAST_STEPS,
    step: str = FORECAST_PERIOD,
) -> Series:
    """Multistep recursive forecasting using the input time series data and a pre-trained machine learning model

    Parameters
    ----------
    city_name: The name of the city where the sensor is located
    sensor_id: The ID of the sensor to fetch weather data
    pollutant: The pollutant that is used as a forecasting target
    model: An already trained machine learning model implementing the scikit-learn interface
    model_features: Selected model features for forecasting
    lags: List of lags used for training the model
    n_steps: Number of time periods in the forecasting horizon
    step: The period of forecasting

    Returns
    -------
    forecast_values: pd.Series with forecasted values indexed by forecast horizon dates
    """

    upcoming_hour = next_hour(current_hour())
    forecast_range = date_range(upcoming_hour, periods=n_steps, freq=step)

    dataframe = fetch_summary_dataframe(
        DATA_PROCESSED_PATH / city_name / sensor_id, index_col="time"
    )
    if len(dataframe.index) == 0:
        return Series()

    dataframe = dataframe.loc[datetime.now() - timedelta(weeks=52) : datetime.now()]
    target = dataframe[pollutant].tail(lags * 2 + 1)

    forecasted_values = []
    for date in forecast_range:
        # Build target time series using previously forecast value
        new_point = forecasted_values[-1] if len(forecasted_values) > 0 else 0.0
        target = concat([target, Series(new_point, [date])])

        timestamp = int((date - timedelta(hours=1)).timestamp())
        try:
            data = forecast_sensor(city_name, sensor_id, timestamp)
            features = DataFrame(data, index=[date])
            features = concat([dataframe, features])
            features = features.join(generate_features(target, lags), how="inner")
            features = features[model_features]
            encode_categorical_data(features)
            features = value_scaling(features)
            features = features.tail(1)
            predictions = model.predict(features)
            prediction = predictions[-1]
            forecasted_values.append(prediction if prediction >= 0 else nan)
        except Exception:
            forecasted_values.append(nan)
        target.update(Series(forecasted_values[-1], [target.index[-1]]))
        target = target.tail(lags * 2 + 1)

    forecast_results = Series(forecasted_values, forecast_range)
    return forecast_results.drop(forecast_results.index[0])
