"""Per-sensor ingestion: make the data directories, then fetch into them.

These two functions used to live in ``api/blueprints/__init__.py``, which made the HTTP package
double as a data-access module and left ``api/config/schedule.py`` importing it. A config-layer
module importing the HTTP layer is a layering inversion, and it had a concrete cost: importing
anything under ``modeling`` or ``processing`` standalone pulled in the whole Flask app and died on
a circular import, so the training code could not be exercised without booting the service.

Nothing here touches Flask.
"""

from definitions import DATA_PROCESSED_PATH, DATA_RAW_PATH
from utils import BatchOutcome

from .weather_data import api_is_available, fetch_weather_data


def create_data_paths(city_name: str, sensor_id: str) -> None:
    (DATA_RAW_PATH / city_name / sensor_id).mkdir(parents=True, exist_ok=True)
    (DATA_PROCESSED_PATH / city_name / sensor_id).mkdir(parents=True, exist_ok=True)


def fetch_city_data(city_name: str, sensor: dict) -> BatchOutcome:
    # This guard was `if check_api_lock(): return` for 402 days, which is the inverse of
    # what it needed: that function returned `not lock_file.exists()`, so True meant the
    # API was AVAILABLE and the early return fired exactly when there was work to do. The
    # predicate is now named for its polarity, which is what stops the line being written
    # backwards again -- `if not api_is_available()` cannot be misread the way
    # `if check_api_lock()` could.
    if not api_is_available():
        return BatchOutcome.SKIPPED
    create_data_paths(city_name, sensor["sensorId"])
    return (
        BatchOutcome.DONE
        if fetch_weather_data(city_name, sensor)
        else BatchOutcome.FAILED
    )
