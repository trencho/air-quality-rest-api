from logging import getLogger
from pathlib import Path

from matplotlib import pyplot
from matplotlib.figure import Figure

logger = getLogger(__name__)


def save_plot(fig: Figure, plt: pyplot, file_path: Path, file_name: str) -> None:
    fig.tight_layout()
    file_path.mkdir(parents=True, exist_ok=True)
    save_path = file_path / f"{file_name}.png"
    plt.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Plot saved at {save_path}")
