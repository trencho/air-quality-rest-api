"""Seed processed data for the skopje/1000 sensor so the endpoint integration tests
in ``test_api.py`` can return 200 locally.

In CI/production this data is produced by the scheduler pipeline; a fresh local
checkout only has the raw location JSON, so the history/pollutants endpoints would
(correctly) 404. All four data-dependent tests resolve to skopje/1000 — the two
coordinate tests use that sensor's exact position — so seeding one sensor is enough.

The CSVs are written before the run and removed afterwards, so nothing is committed
and the working tree stays clean.
"""

from pathlib import Path
from shutil import rmtree

import pytest

from definitions import DATA_PROCESSED_PATH

_SENSOR_DIR = DATA_PROCESSED_PATH / "skopje" / "1000"

# Minimal frames: a ``time`` column (history filters on it) plus pollutant columns
# (pollutants lists the ones present). One row is enough — the tests assert only 200.
_SEED_FILES = {
    "pollution.csv": "time,pm2_5,pm10,no2,o3,so2,co\n1704067200,12.0,20.0,15.0,40.0,5.0,0.4\n",
    "weather.csv": "time,temperature,humidity,pressure\n1704067200,7.5,60.0,1013.0\n",
}


def pytest_configure(config: pytest.Config) -> None:
    # Drop any stale FileSystemCache entries (the app caches at /tmp/cache) so a
    # previously cached "data missing" 404 for skopje/1000 can't mask the seed.
    rmtree(Path("/tmp/cache"), ignore_errors=True)

    _SENSOR_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in _SEED_FILES.items():
        (_SENSOR_DIR / name).write_text(content)


def pytest_unconfigure(config: pytest.Config) -> None:
    # Under xdist, clean up only on the controller (workers have ``workerinput``),
    # which finishes after all workers — so the files stay in place while tests run.
    if hasattr(config, "workerinput"):
        return

    for name in _SEED_FILES:
        (_SENSOR_DIR / name).unlink(missing_ok=True)
    # Prune the now-empty dirs we created, stopping at data/processed.
    for directory in (_SENSOR_DIR, _SENSOR_DIR.parent):
        try:
            directory.rmdir()
        except OSError:
            break
