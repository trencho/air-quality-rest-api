from os import path

import seaborn
from matplotlib import pyplot
from pandas import DataFrame, read_csv

from definitions import pollutants, regression_models, RESULTS_ERRORS_PATH
from .handle_plot import save_plot


def draw_errors(city: dict, sensor: dict, pollutant: str) -> None:
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
    pyplot.rcParams.update(params)
    pyplot.style.use('seaborn-whitegrid')
    seaborn.set_style('white')

    for error_type in error_types:
        data = []
        for model_name in regression_models:
            dataframe_errors = read_csv(
                path.join(RESULTS_ERRORS_PATH, 'data', city['cityName'], sensor['sensorId'], pollutant, model_name,
                          'error.csv'))
            data.append([regression_models[model_name], dataframe_errors.iloc[0][error_type]])

        dataframe_algorithms = DataFrame(data, columns=['algorithm', pollutant]).dropna()
        if len(dataframe_algorithms.index) == 0:
            continue

        dataframe_algorithms.sort_values(by=pollutant, ascending=False, inplace=True)
        dataframe_algorithms.reset_index(drop=True, inplace=True)

        fig, ax = pyplot.subplots(figsize=(16, 10), facecolor='white', dpi=80)
        ax.vlines(x=dataframe_algorithms.index, ymin=0, ymax=dataframe_algorithms[pollutant], color='firebrick',
                  alpha=0.7, linewidth=40, label=pollutants[pollutant])
        ax.legend()

        for i, value in enumerate(dataframe_algorithms[pollutant]):
            ax.text(i, value + 0.5, round(value, 1), fontsize=22, horizontalalignment='center')

        ax.set_title(f'{city["siteName"]} - {sensor["description"]}', fontdict={'size': 22})
        ax.set_ylabel(error_type, fontsize=22)
        y_lim = dataframe_algorithms[pollutant].max() + 10 - (dataframe_algorithms[pollutant].max() % 10)
        ax.set_ylim(ymin=0, ymax=y_lim)
        pyplot.xticks(dataframe_algorithms.index, dataframe_algorithms['algorithm'], horizontalalignment='center',
                      fontsize=22, rotation=30)

        save_plot(fig, pyplot, path.join(RESULTS_ERRORS_PATH, 'plots', city['cityName'], sensor['sensorId'], pollutant),
                  error_type)
