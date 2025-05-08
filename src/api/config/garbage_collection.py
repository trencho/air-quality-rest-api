from gc import collect, freeze, get_threshold, set_threshold
from logging import getLogger

logger = getLogger(__name__)


def init_gc() -> None:
    collect()
    freeze()
    _, g1, g2 = get_threshold()
    THRESHOLD_0 = 100_000
    new_threshold_1 = g1 * 5
    new_threshold_2 = g2 * 10
    set_threshold(THRESHOLD_0, new_threshold_1, new_threshold_2)
    logger.info(
        f"GC thresholds set to: {THRESHOLD_0}, {g1 * new_threshold_1}, {g2 * new_threshold_2}"
    )
