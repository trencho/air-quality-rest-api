from gc import collect, freeze, get_threshold, set_threshold
from logging import getLogger

# Constants for threshold values
THRESHOLD_0 = 100_000
THRESHOLD_MULTIPLIER_1 = 5
THRESHOLD_MULTIPLIER_2 = 10

logger = getLogger(__name__)


def configure_gc() -> None:
    collect()
    freeze()
    _, g1, g2 = get_threshold()
    new_threshold_1 = g1 * THRESHOLD_MULTIPLIER_1
    new_threshold_2 = g2 * THRESHOLD_MULTIPLIER_2
    set_threshold(THRESHOLD_0, new_threshold_1, new_threshold_2)
    logger.info(f"GC thresholds set to: {THRESHOLD_0}, {g1 * new_threshold_1}, {g2 * new_threshold_2}")
