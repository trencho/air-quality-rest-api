"""Hermetic contract tests for ``InMemoryRepository`` (no Mongo, no network).

The in-memory repository is the dev/test backend and must honour the same contract the
blueprints rely on. This locks in save/get/get_many/save_many/delete behaviour and
guards a real bug: ``get_many`` filtered on ``item.__dict__``, which a plain ``dict``
doesn't have — so filtering stored records raised ``AttributeError``. The app stores
every collection (cities/countries/sensors/weather/pollution) as dicts and feeds
``get_many``'s result straight into a ``DataFrame`` (see ``processing/handle_data.py``).
"""

import pytest

from api.config.repository import InMemoryRepository


@pytest.fixture
def repo() -> InMemoryRepository:
    return InMemoryRepository()


def test_save_then_get_by_filter(repo):
    item = {"sensorId": "1000", "value": 42}
    repo.save("weather", filter={"sensorId": "1000"}, item=item)
    assert repo.get("weather", filter={"sensorId": "1000"}) == item


def test_get_missing_returns_none(repo):
    assert repo.get("weather", filter={"sensorId": "nope"}) is None


def test_save_with_filter_updates_in_place(repo):
    repo.save(
        "sensors",
        filter={"sensorId": "1000"},
        item={"sensorId": "1000", "status": "ACTIVE"},
    )
    repo.save(
        "sensors",
        filter={"sensorId": "1000"},
        item={"sensorId": "1000", "status": "INACTIVE"},
    )
    matches = repo.get_many("sensors", filter={"sensorId": "1000"})
    assert len(matches) == 1
    assert matches[0]["status"] == "INACTIVE"


def test_get_many_with_filter_returns_matching_dicts(repo):
    # Regression: dict items have no __dict__, so filtering used to raise AttributeError.
    repo.save("weather", filter={"sensorId": "1000"}, item={"sensorId": "1000", "t": 1})
    repo.save("weather", filter={"sensorId": "2000"}, item={"sensorId": "2000", "t": 2})
    matches = repo.get_many("weather", filter={"sensorId": "1000"})
    assert [m["t"] for m in matches] == [1]


def test_get_many_without_filter_returns_all(repo):
    repo.save("weather", filter={"sensorId": "1000"}, item={"sensorId": "1000"})
    repo.save("weather", filter={"sensorId": "2000"}, item={"sensorId": "2000"})
    assert len(repo.get_many("weather")) == 2


def test_get_many_no_match_returns_empty(repo):
    repo.save("weather", filter={"sensorId": "1000"}, item={"sensorId": "1000"})
    assert repo.get_many("weather", filter={"sensorId": "nope"}) == []


def test_get_many_empty_collection_returns_empty(repo):
    assert repo.get_many("weather", filter={"sensorId": "1000"}) == []
    assert repo.get_many("weather") == []


def test_save_many_then_get_and_delete(repo):
    items = [{"sensorId": "1000", "t": 1}, {"sensorId": "1000", "t": 2}]
    repo.save_many("pollution", items)
    stored = repo.get_many("pollution", filter={"sensorId": "1000"})
    assert len(stored) == 2

    repo.delete("pollution", stored[0])
    remaining = repo.get_many("pollution", filter={"sensorId": "1000"})
    assert len(remaining) == 1
