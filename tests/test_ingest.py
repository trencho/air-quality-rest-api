"""Tests for ``preparation.ingest``: per-sensor path creation and the fetch guard.

These moved out of ``tests/test_blueprints.py`` with the functions themselves. They used to live
in ``api/blueprints/__init__.py``, which made the HTTP package double as a data-access module and
left ``api/config/schedule.py`` importing it -- a layering inversion whose concrete cost was that
``modeling`` and ``processing`` could not be imported without booting Flask.
"""

import api.config  # noqa: F401
from preparation import ingest
from utils import BatchOutcome

# --- api.ingest.fetch_city_data -------------------------------------------------


def test_fetch_city_data_fetches_when_the_api_is_unlocked(monkeypatch, tmp_path):
    """The guard was inverted, so this never fetched anything.

    The predicate is ``api_is_available()`` now; it was ``check_api_lock()``, which reads
    as "is it locked?" while returning ``not lock_file.exists()`` -- the opposite. This
    guard was written ``if check_api_lock(): return``, the exact inverse of the one in its
    only caller (``fetch_hourly_data`` bailed on ``not check_api_lock()``), so it returned
    immediately whenever OpenWeather was callable and was only ever reached when the outer
    job had already bailed: it fetched nothing under either condition, for 402 days.

    Nothing failed and nothing raised, which is why it survived. The tally in
    ``fetch_hourly_data`` is what would have shown it -- every sensor skipped, every run.
    The rename is what stops it recurring: ``if not api_is_available()`` cannot be misread.
    """
    monkeypatch.setattr(ingest, "DATA_RAW_PATH", tmp_path / "raw")
    monkeypatch.setattr(ingest, "DATA_PROCESSED_PATH", tmp_path / "processed")
    monkeypatch.setattr(ingest, "api_is_available", lambda: True)  # unlocked
    calls = []
    monkeypatch.setattr(
        ingest,
        "fetch_weather_data",
        lambda city_name, sensor: calls.append((city_name, sensor["sensorId"])) or True,
    )

    outcome = ingest.fetch_city_data("skopje", {"sensorId": "1000"})

    assert calls == [("skopje", "1000")], "an unlocked API must actually be fetched"
    assert outcome is BatchOutcome.DONE


def test_fetch_city_data_skips_when_the_api_is_locked(monkeypatch, tmp_path):
    monkeypatch.setattr(ingest, "DATA_RAW_PATH", tmp_path / "raw")
    monkeypatch.setattr(ingest, "DATA_PROCESSED_PATH", tmp_path / "processed")
    monkeypatch.setattr(ingest, "api_is_available", lambda: False)  # locked
    calls = []
    monkeypatch.setattr(
        ingest,
        "fetch_weather_data",
        lambda city_name, sensor: calls.append(sensor) or True,
    )

    outcome = ingest.fetch_city_data("skopje", {"sensorId": "1000"})

    assert calls == [], "a locked API must not be called"
    # SKIPPED, not DONE: a run that fetched nothing because the quota is spent is not a
    # successful run, and the tally has to be able to say which it was.
    assert outcome is BatchOutcome.SKIPPED


def test_fetch_city_data_reports_a_failed_fetch(monkeypatch, tmp_path):
    monkeypatch.setattr(ingest, "DATA_RAW_PATH", tmp_path / "raw")
    monkeypatch.setattr(ingest, "DATA_PROCESSED_PATH", tmp_path / "processed")
    monkeypatch.setattr(ingest, "api_is_available", lambda: True)
    monkeypatch.setattr(ingest, "fetch_weather_data", lambda *args: False)

    assert ingest.fetch_city_data("skopje", {"sensorId": "1000"}) is BatchOutcome.FAILED
