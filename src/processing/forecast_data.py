from os import path

from pandas import concat as pandas_concat, DataFrame, date_range, read_csv, Series, Timedelta

from api.config.cache import cache
from definitions import DATA_EXTERNAL_PATH
from .feature_generation import encode_categorical_data, generate_features, generate_lag_features, \
    generate_time_features
from .feature_scaling import value_scaling

FORECAST_PERIOD = '1H'
FORECAST_STEPS = 1


@cache.memoize(timeout=3600)
def forecast_sensor(city_name, sensor_id, timestamp):
    dataframe = read_csv(path.join(DATA_EXTERNAL_PATH, city_name, sensor_id, 'weather.csv'))
    dataframe = dataframe.loc[dataframe['time'] == timestamp]
    if not dataframe.empty:
        return dataframe.to_dict('records')[0]
    return {}


def direct_forecast(y, model, lags=FORECAST_STEPS, n_steps=FORECAST_STEPS, step=FORECAST_PERIOD) -> Series:
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

    def one_step_features(date, step):
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


def recursive_forecast(y, city_name, sensor_id, model, model_features, n_steps=FORECAST_STEPS,
                       step=FORECAST_PERIOD) -> Series:
    """Multi-step recursive forecasting using the input time series data and a pre-trained machine learning model

    Parameters
    ----------
    y: pd.Series holding the input time-series to forecast
    city_name: The name of the city where the sensor is located
    sensor_id: The ID of the sensor to forecast weather data
    model: An already trained machine learning model implementing the scikit-learn interface
    model_features: Selected model features for forecasting
    n_steps: Number of time periods in the forecasting horizon
    step: The period of forecasting

    Returns
    -------
    forecast_values: pd.Series with forecasted values indexed by forecast horizon dates
    """

    # Get the dates to forecast
    last_date = y.index[-1] + Timedelta(hours=1)
    forecast_range = date_range(last_date, periods=n_steps, freq=step)

    forecasted_values = []
    target = y.copy()

    for date in forecast_range:
        # Build target time series using previously forecast value
        new_point = forecasted_values[-1] if len(forecasted_values) > 0 else 0.0
        target = target.append(Series(index=[date], data=new_point))

        # Forecast
        timestamp = int((date - Timedelta(hours=1)).timestamp())
        forecast_data = forecast_sensor(city_name, sensor_id, timestamp)
        data = {}
        for model_feature in model_features:
            feature_value = forecast_data.get(model_feature)
            if feature_value is not None:
                data[model_feature] = feature_value

        dataframe = DataFrame(data, index=[date])
        dataframe = dataframe.join(generate_features(target), how='inner').dropna()
        dataframe = pandas_concat(
            [dataframe, DataFrame(columns=list(set(model_features) - set(list(dataframe.columns))))])
        encode_categorical_data(dataframe)
        dataframe = dataframe[model_features]
        dataframe = value_scaling(dataframe)
        predictions = model.predict(dataframe)
        forecasted_values.append(predictions[-1])
        target.update(Series(forecasted_values[-1], index=[target.index[-1]]))

    return Series(forecasted_values, forecast_range)
