from datetime import datetime
from math import isnan, nan
from os import path
from pickle import load as pickle_load
from typing import Optional

from pandas import concat as pandas_concat, DataFrame, date_range, read_csv, Series, Timedelta, to_datetime

from api.config.cache import cache
from definitions import DATA_PROCESSED_PATH, MODELS_PATH, pollutants
from modeling import train_city_sensors
from models.base_regression_model import BaseRegressionModel
from .feature_generation import encode_categorical_data, generate_lag_features, generate_time_features
from .feature_scaling import value_scaling
from .normalize_data import next_hour

FORECAST_PERIOD = '1H'
FORECAST_STEPS = 24


def fetch_forecast_result(city: dict, sensor: dict) -> dict:
    forecast_result = {}
    for pollutant in pollutants:
        if (predictions := forecast_city_sensor(city, sensor, pollutant)) is None:
            continue

        for index, value in predictions.items():
            timestamp_dict = forecast_result.get(int(index.timestamp()), {})
            timestamp_dict.update({'time': int(index.timestamp()), pollutant: None if isnan(value) else value})
            forecast_result.update({int(index.timestamp()): timestamp_dict})

    return forecast_result


@cache.memoize(timeout=3600)
def fetch_weather_features(city_name: str, sensor_id: str, model_features: list, timestamp: int) -> dict:
    forecast_data = forecast_sensor(city_name, sensor_id, timestamp)
    data = {}
    for model_feature in model_features:
        if (feature_value := forecast_data.get(model_feature)) is not None:
            data[model_feature] = feature_value

    return data


@cache.memoize(timeout=3600)
def forecast_city_sensor(city: dict, sensor: dict, pollutant: str) -> Optional[Series]:
    if (load_model := load_regression_model(city, sensor, pollutant)) is None:
        return load_model

    model, model_features = load_model

    return recursive_forecast(city['cityName'], sensor['sensorId'], pollutant, model, model_features)


@cache.memoize(timeout=3600)
def forecast_sensor(city_name: str, sensor_id: str, timestamp: int) -> dict:
    dataframe = read_csv(path.join(DATA_PROCESSED_PATH, city_name, sensor_id, 'weather.csv'))
    dataframe = dataframe.loc[dataframe['time'] == timestamp]
    if not dataframe.empty:
        return dataframe.to_dict('records')[0]

    return {}


@cache.memoize(timeout=3600)
def load_regression_model(city: dict, sensor: dict, pollutant: str) -> Optional[tuple]:
    if not path.exists(
            path.join(MODELS_PATH, city['cityName'], sensor['sensorId'], pollutant, 'best_regression_model.pkl')):
        train_city_sensors(city, sensor, pollutant)
        return None

    with open(path.join(MODELS_PATH, city['cityName'], sensor['sensorId'], pollutant, 'best_regression_model.pkl'),
              'rb') as in_file:
        model = pickle_load(in_file)

    with open(path.join(MODELS_PATH, city['cityName'], sensor['sensorId'], pollutant, 'selected_features.pkl'),
              'rb') as in_file:
        model_features = pickle_load(in_file)

    return model, model_features


@cache.memoize(timeout=3600)
def direct_forecast(y: Series, model: BaseRegressionModel, lags: int = FORECAST_STEPS, n_steps: int = FORECAST_STEPS,
                    step: str = FORECAST_PERIOD) -> Series:
    """Multi-step direct forecasting using a machine learning model to forecast each time period ahead

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
        # Features must be obtained using data lagged by the desired number of steps (the for loop index)
        tmp = y[y.index <= date]
        lags_features = generate_lag_features(tmp, lags)
        time_features = generate_time_features(tmp)
        features = lags_features.join(time_features, how='inner').dropna()

        # Build target to be ahead of the features built by the desired number of steps (the for loop index)
        target = y[y.index >= features.index[0] + Timedelta(hours=step)]
        assert len(features.index) == len(target.index)

        return features, target

    forecast_values = []
    forecast_range = date_range(y.index[-1] + Timedelta(hours=1), periods=n_steps, freq=step)
    forecast_features, _ = one_step_features(y.index[-1], 0)

    for s in range(1, n_steps + 1):
        last_date = y.index[-1] - Timedelta(hours=s)
        features, target = one_step_features(last_date, s)

        model.train(features, target)

        # Use the model to predict s steps ahead
        predictions = model.predict(forecast_features)
        forecast_values.append(predictions[-1])

    return Series(forecast_values, forecast_range)


@cache.memoize(timeout=3600)
def recursive_forecast(city_name: str, sensor_id: str, pollutant: str, model: BaseRegressionModel, model_features: list,
                       lags: int = FORECAST_STEPS, n_steps: int = FORECAST_STEPS,
                       step: str = FORECAST_PERIOD) -> Series:
    """Multi-step recursive forecasting using the input time series data and a pre-trained machine learning model

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

    # Get the hours to forecast
    upcoming_hour = next_hour(datetime.now())
    forecast_range = date_range(upcoming_hour, periods=n_steps, freq=step)

    forecasted_values = []
    dataframe = read_csv(path.join(DATA_PROCESSED_PATH, city_name, sensor_id, 'summary.csv'), index_col='time')
    dataframe.index = to_datetime(dataframe.index, unit='s')
    target = dataframe[pollutant].copy()

    for date in forecast_range:
        # Build target time series using previously forecast value
        new_point = forecasted_values[-1] if len(forecasted_values) > 0 else 0.0
        target = target.append(Series(new_point, [date]))

        timestamp = int((date - Timedelta(hours=1)).timestamp())
        if not (data := fetch_weather_features(city_name, sensor_id, model_features, timestamp)):
            forecasted_values.append(nan)
            target.update(Series(forecasted_values[-1], [target.index[-1]]))
            continue

        dataframe = DataFrame(data, index=[date])
        lags_features = generate_lag_features(target, lags)
        time_features = generate_time_features(target)
        features = dataframe.join(lags_features, how='inner').join(time_features, how='inner')
        features = pandas_concat([features, DataFrame(columns=list(set(model_features) - set(list(features.columns))))])
        encode_categorical_data(features)
        features = features[model_features]
        try:
            features = value_scaling(features)
            predictions = model.predict(features)
            forecasted_values.append(predictions[-1])
        except ValueError:
            forecasted_values.append(nan)
        target.update(Series(forecasted_values[-1], [target.index[-1]]))

    return Series(forecasted_values, forecast_range)
