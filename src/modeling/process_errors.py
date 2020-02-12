import numpy as np
import pandas as pd
from sklearn import metrics

from definitions import RESULTS_ERRORS_PATH


def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def save_errors(model_name, city_name, sensor, pollutant, y_test, y_pred):
    df = pd.DataFrame({'Mean Absolute Error': [metrics.mean_absolute_error(y_test, y_pred)],
                       'Mean Absolute Percentage Error': [mean_absolute_percentage_error(y_test, y_pred)],
                       'Mean Squared Error': [metrics.mean_squared_error(y_test, y_pred)],
                       'Root Mean Squared Error': [np.sqrt(metrics.mean_squared_error(y_test, y_pred))]},
                      columns=['Mean Absolute Error', 'Mean Absolute Percentage Error', 'Mean Squared Error',
                               'Root Mean Squared Error'])
    df.to_csv(RESULTS_ERRORS_PATH + '/data/' + city_name + '/' + sensor['sensorId'] + '/' + pollutant + '/' + model_name
              + '/error.csv', index=False)

    return metrics.mean_absolute_error(y_test, y_pred)
