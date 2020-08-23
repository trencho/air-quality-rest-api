from pandas import date_range, Series, Timedelta

from processing import generate_lag_features, generate_time_features

FORECAST_PERIOD = '1H'
FORECAST_STEPS = 48


def direct(y, train_fn, params=None, lags=FORECAST_STEPS, n_steps=FORECAST_STEPS, step=FORECAST_PERIOD):
    """Multi-step direct forecasting using a machine learning model to forecast each time period ahead

    Parameters
    ----------
    y: pd.Series holding the input time-series to forecast
    train_fn: A function for training the model which returns as output the trained model cross-validation score and
    test score
    params: Additional parameters for the training function
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
        features = lags_features.join(time_features, how='outer').dropna()

        # Build target to be ahead of the features built by the desired number of steps (the for loop index)
        target = y[y.index >= features.index[0] + Timedelta(hours=step)]
        assert len(features.index) == len(target.index)

        return features, target

    params = {} if params is None else params
    forecast_values = []
    forecast_range = date_range(y.index[-1] + Timedelta(hours=1), periods=n_steps, freq=step)
    forecast_features, _ = one_step_features(y.index[-1], 0)

    for s in range(1, n_steps + 1):
        last_date = y.index[-1] - Timedelta(hours=s)
        features, target = one_step_features(last_date, s)

        model, cv_score, test_score = train_fn(features, target, **params)

        # Use the model to predict s steps ahead
        predictions = model.predict(forecast_features)
        forecast_values.append(predictions[-1])

    return Series(index=forecast_range, data=forecast_values)


def recursive(y, model, lags, n_steps=FORECAST_STEPS, step=FORECAST_PERIOD):
    """Multi-step recursive forecasting using the input time series data and a pre-trained machine learning model

    Parameters
    ----------
    y: pd.Series holding the input time-series to forecast
    model: an already trained machine learning model implementing the scikit-learn interface
    lags: List of lags used for training the model
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
        time_features = generate_time_features(target)
        lags_features = generate_lag_features(target, lags)
        features = time_features.join(lags_features, how='outer').dropna()

        predictions = model.predict(features)
        forecasted_values.append(predictions[-1])

    return Series(index=forecast_range, data=forecasted_values)
