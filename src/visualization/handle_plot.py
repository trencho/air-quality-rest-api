from datetime import datetime
from os import makedirs, path

from definitions import RESULTS_PREDICTIONS_PATH


def save_plot(fig, plt, city_name, sensor_id, pollutant, file_name):
    fig.tight_layout()

    if not path.exists(path.join(RESULTS_PREDICTIONS_PATH, 'plots', city_name, sensor_id, pollutant)):
        makedirs(path.join(RESULTS_PREDICTIONS_PATH, 'plots', city_name, sensor_id, pollutant))
    plt.savefig(path.join(RESULTS_PREDICTIONS_PATH, 'plots', city_name, sensor_id, pollutant,
                          f'{file_name} - {datetime.now().strftime("%H:%M:%S %d-%m-%Y")}.png'),
                bbox_inches='tight')
    plt.close(fig)
