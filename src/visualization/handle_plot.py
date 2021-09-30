from os import makedirs, path

from matplotlib import pyplot
from matplotlib.figure import Figure


def save_plot(fig: Figure, plt: pyplot, file_path: str, file_name: str) -> None:
    fig.tight_layout()

    makedirs(file_path, exist_ok=True)
    plt.savefig(path.join(file_path, f'{file_name}.png'), bbox_inches='tight')
    plt.close(fig)
