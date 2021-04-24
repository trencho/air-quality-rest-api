from os import path
from warnings import filterwarnings

import seaborn as sns
from matplotlib import pyplot as plt
from pandas import DataFrame, read_csv

from definitions import pollutants, regression_models, RESULTS_ERRORS_PATH
from .handle_plot import save_plot

filterwarnings(action='once')


def draw_errors(city, sensor, pollutant):
    error_types = [
        'Mean Absolute Error',
        'Mean Absolute Percentage Error',
        'Mean Squared Error',
        'Root Mean Squared Error'
    ]

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
                path.join(RESULTS_ERRORS_PATH, 'data', city['cityName'], sensor['sensorId'], pollutant, algorithm,
                          'error.csv'))
            dataframe_algorithms = dataframe_algorithms.append(
                [{
                    'algorithm': regression_models[algorithm],
                    pollutant: dataframe_errors.iloc[0][error_type]
                }], ignore_index=True).dropna()

        if dataframe_algorithms.empty:
            continue

        dataframe_algorithms.sort_values(by=pollutant, ascending=False, inplace=True)
        dataframe_algorithms.reset_index(drop=True, inplace=True)

        fig, ax = plt.subplots(figsize=(16, 10), facecolor='white', dpi=80)
        ax.vlines(x=dataframe_algorithms.index, ymin=0, ymax=dataframe_algorithms[pollutant], color='firebrick',
                  alpha=0.7, linewidth=40, label=pollutants[pollutant])
        ax.legend()

        # Annotate Text
        for i, value in enumerate(dataframe_algorithms[pollutant]):
            ax.text(i, value + 0.5, round(value, 1), fontsize=22, horizontalalignment='center')

        # Title, Label, Ticks and Ylim
        ax.set_title(f'{city["siteName"]} - {sensor["description"]}', fontdict={'size': 22})
        ax.set_ylabel(error_type, fontsize=22)
        y_lim = dataframe_algorithms[pollutant].max() + 10 - (dataframe_algorithms[pollutant].max() % 10)
        ax.set_ylim(ymin=0, ymax=y_lim)
        plt.xticks(dataframe_algorithms.index, dataframe_algorithms['algorithm'], horizontalalignment='center',
                   fontsize=22, rotation=30)

        file_path = path.join(RESULTS_ERRORS_PATH, 'plots', city['cityName'], sensor['sensorId'], pollutant)
        save_plot(fig, plt, file_path, error_type)
