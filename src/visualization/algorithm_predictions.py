import os
import warnings

import matplotlib.pyplot as plt
import pandas as pd

from definitions import DATA_EXTERNAL_PATH, RESULTS_ERRORS_PATH, RESULTS_PREDICTIONS_PATH, regression_models

warnings.filterwarnings(action='once')


def previous_value_overwrite(X):
    X = X.shift(periods=-1, axis=0)
    X.reset_index(drop=True, inplace=True)
    X.drop(len(X) - 1, inplace=True)

    return X


def draw_predictions(city, sensor, pollutant):
    dataset = pd.read_csv(
        DATA_EXTERNAL_PATH + '/' + city['cityName'] + '/' + sensor['sensorId'] + '/summary_report.csv')
    validation_split = len(dataset) * 3 // 4

    test_dataset = dataset.iloc[validation_split:]
    test_dataset.reset_index(drop=True, inplace=True)

    dataframe_algorithms = pd.DataFrame(columns=['algorithm', pollutant])
    for algorithm in regression_models:
        dataframe_errors = pd.read_csv(RESULTS_ERRORS_PATH + '/data/' + city['cityName'] + '/' + sensor['sensorId']
                                       + '/' + pollutant + '/' + algorithm + '/error.csv')
        dataframe_algorithms = dataframe_algorithms.append(
            [{'algorithm': algorithm, pollutant: dataframe_errors.iloc[0]['Mean Absolute Error']}], ignore_index=True)

    algorithm_index = dataframe_algorithms[pollutant].idxmin()
    dataframe_predictions = pd.read_csv(
        RESULTS_PREDICTIONS_PATH + '/data/' + city['cityName'] + '/' + sensor['sensorId'] + '/' + pollutant + '/'
        + dataframe_algorithms.iloc[algorithm_index]['algorithm'] + '/prediction.csv')

    X_test = test_dataset.drop(columns=pollutant, errors='ignore')
    X_test = previous_value_overwrite(X_test)
    x = X_test['time']
    x = pd.to_datetime(x, unit='s').dt.normalize()

    y1 = dataframe_predictions['Actual']
    y2 = dataframe_predictions['Predicted']

    # Plot Line (left Y axis)
    fig, ax = plt.subplots(1, 1, figsize=(16, 10), dpi=80)
    ax.plot(x, y1, color='tab:red', label='Actual')
    ax.plot(x, y2, color='tab:green',
            label='Predicted: ' + regression_models[dataframe_algorithms.iloc[algorithm_index]['algorithm']])
    # Decorations
    # ax (left Y axis)
    ax.set_xlabel('Dates', fontsize=22)
    ax.tick_params(axis='x', rotation=0, labelsize=18)
    ax.set_ylabel(pollutant + ' values', fontsize=22)
    ax.tick_params(axis='y', rotation=0)
    ax.set_title(city['siteName'] + ' - ' + sensor['description'], fontsize=22)
    ax.grid(alpha=.4)
    ax.legend(fontsize=16)

    fig.tight_layout()
    plt.gcf().autofmt_xdate()

    if not os.path.exists(
            RESULTS_PREDICTIONS_PATH + '/plots/' + city['cityName'] + '/' + sensor['sensorId'] + '/' + pollutant):
        os.makedirs(
            RESULTS_PREDICTIONS_PATH + '/plots/' + city['cityName'] + '/' + sensor['sensorId'] + '/' + pollutant)
    plt.savefig(RESULTS_PREDICTIONS_PATH + '/plots/' + city['cityName'] + '/' + sensor['sensorId'] + '/' + pollutant
                + '/predictions.png', bbox_inches='tight')
    plt.close(fig)
