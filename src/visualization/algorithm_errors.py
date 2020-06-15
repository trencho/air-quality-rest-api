import warnings
from os import makedirs, path

import matplotlib.pyplot as plt
import seaborn as sns
from pandas import DataFrame, read_csv

from definitions import RESULTS_ERRORS_PATH, regression_models

warnings.filterwarnings(action='once')


def draw_errors(city, sensor, pollutant):
    error_types = ['Mean Absolute Error', 'Mean Squared Error', 'Root Mean Squared Error']

    large, med, small = 22, 16, 12
    params = {
        'legend.fontsize': med,
        'figure.figsize': (16, 10),
        'axes.labelsize': med,
        'axes.titlesize': med,
        'xtick.labelsize': med,
        'ytick.labelsize': med,
        'figure.titlesize': large,
        'xtick.major.pad': 8
    }
    plt.rcParams.update(params)
    plt.style.use('seaborn-whitegrid')
    sns.set_style('white')

    for error_type in error_types:
        dataframe_algorithms = DataFrame(columns=['algorithm', pollutant])
        for algorithm in regression_models:
            dataframe_errors = read_csv(
                RESULTS_ERRORS_PATH + '/data/' + city['cityName'] + '/' + sensor['sensorId'] + '/' + pollutant + '/'
                + algorithm + '/error.csv')
            dataframe_algorithms = dataframe_algorithms.append(
                [{'algorithm': regression_models[algorithm], pollutant: dataframe_errors.iloc[0][error_type]}],
                ignore_index=True)

        dataframe_algorithms.sort_values(by=pollutant, ascending=False, inplace=True)
        dataframe_algorithms.reset_index(drop=True, inplace=True)

        fig, ax = plt.subplots(figsize=(16, 10), facecolor='white', dpi=80)
        ax.vlines(x=dataframe_algorithms.index, ymin=0, ymax=dataframe_algorithms[pollutant], color='firebrick',
                  alpha=0.7, linewidth=40, label=pollutant)
        ax.legend()

        # Annotate Text
        for i, value in enumerate(dataframe_algorithms[pollutant]):
            ax.text(i, value + 0.5, round(value, 1), fontsize=22, horizontalalignment='center')

        y_lim = dataframe_algorithms[pollutant].max() + 10 - (dataframe_algorithms[pollutant].max() % 10)
        # Title, Label, Ticks and Ylim
        ax.set_title(city['siteName'] + ' - ' + sensor['description'], fontdict={'size': 22})
        ax.set_ylabel(error_type, fontsize=22)
        ax.set_ylim(ymin=0, ymax=y_lim)
        plt.xticks(dataframe_algorithms.index, dataframe_algorithms['algorithm'], horizontalalignment='center',
                   fontsize=22, rotation=30)

        fig.tight_layout()
        if not path.exists(
                RESULTS_ERRORS_PATH + '/plots/' + city['cityName'] + '/' + sensor['sensorId'] + '/' + pollutant):
            makedirs(RESULTS_ERRORS_PATH + '/plots/' + city['cityName'] + '/' + sensor['sensorId'] + '/' + pollutant)
        plt.savefig(RESULTS_ERRORS_PATH + '/plots/' + city['cityName'] + '/' + sensor['sensorId'] + '/' + pollutant
                    + '/' + error_type + '.png', bbox_inches='tight')
        plt.close(fig)
