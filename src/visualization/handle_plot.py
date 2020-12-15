from datetime import datetime
from os import makedirs, path


def save_plot(fig, plt, file_path, file_name):
    fig.tight_layout()

    if not path.exists(file_path):
        makedirs(file_path)
    plt.savefig(path.join(file_path, f'{file_name} - {datetime.now().strftime("%H-%M-%S %d-%m-%Y")}.png'),
                bbox_inches='tight')
    plt.close(fig)
