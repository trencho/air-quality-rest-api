from gc import collect, freeze, get_threshold, set_threshold


def configure_gc() -> None:
    collect()
    freeze()
    _, g1, g2 = get_threshold()
    set_threshold(100_000, g1 * 5, g2 * 10)
