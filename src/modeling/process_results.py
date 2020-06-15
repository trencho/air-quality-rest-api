from numpy import abs, array, mean, sqrt
from pandas import DataFrame
from sklearn import metrics

from definitions import RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH


def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = array(y_true), array(y_pred)
    return mean(abs((y_true - y_pred) / y_true)) * 100


def save_errors(city_name, sensor_id, pollutant, model_name, y_test, y_pred):
    df = DataFrame({'Mean Absolute Error': [metrics.mean_absolute_error(y_test, y_pred)],
                    'Mean Absolute Percentage Error': [mean_absolute_percentage_error(y_test, y_pred)],
                    'Mean Squared Error': [metrics.mean_squared_error(y_test, y_pred)],
                    'Root Mean Squared Error': [sqrt(metrics.mean_squared_error(y_test, y_pred))]},
                   columns=['Mean Absolute Error', 'Mean Absolute Percentage Error', 'Mean Squared Error',
                            'Root Mean Squared Error'])
    df.to_csv(RESULTS_ERRORS_PATH + '/data/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + model_name
              + '/error.csv', index=False)

    return metrics.mean_absolute_error(y_test, y_pred)


def save_results(city_name, sensor_id, pollutant, model_name, y_test, y_pred):
    df = DataFrame({'Actual': y_test, 'Predicted': y_pred})
    df.to_csv(RESULTS_PREDICTIONS_PATH + '/data/' + city_name + '/' + sensor_id + '/' + pollutant + '/' + model_name
              + '/prediction.csv', index=False)
