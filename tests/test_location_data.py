"""Hermetic tests for country coverage in ``preparation.location_data``.

``requests.get`` is mocked so ``fetch_cities`` never hits pulse.eco; the tests assert
which countries pass the ENABLED_COUNTRIES filter.
"""

# Import the config package first so the api/preparation chain initialises in order.
import api.config  # noqa: F401
from definitions import COUNTRIES, ENABLED_COUNTRIES
from preparation.location_data import enabled_country_codes, fetch_cities


def test_enabled_country_codes_defaults_to_all_supported(monkeypatch):
    monkeypatch.delenv(ENABLED_COUNTRIES, raising=False)
    assert enabled_country_codes() == set(COUNTRIES)


def test_enabled_country_codes_parses_env(monkeypatch):
    monkeypatch.setenv(ENABLED_COUNTRIES, "mk, rs ,bg")
    assert enabled_country_codes() == {"MK", "RS", "BG"}


def _city(name: str, code: str) -> dict:
    return {
        "cityName": name,
        "countryCode": code,
        "cityBorderPoints": [
            {"latitude": "42.0", "longitute": "21.4"},
            {"latitude": "42.1", "longitute": "21.5"},
            {"latitude": "42.0", "longitute": "21.6"},
        ],
    }


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_fetch_cities_filters_to_enabled_countries(monkeypatch):
    payload = [_city("skopje", "MK"), _city("belgrade", "RS"), _city("zurich", "CH")]
    monkeypatch.setattr(
        "preparation.location_data.get", lambda url: _FakeResponse(payload)
    )
    monkeypatch.setenv(ENABLED_COUNTRIES, "MK,RS")

    cities = fetch_cities()
    assert {city["countryCode"] for city in cities} == {"MK", "RS"}


def test_fetch_cities_default_covers_all_supported(monkeypatch):
    monkeypatch.delenv(ENABLED_COUNTRIES, raising=False)
    payload = [_city("skopje", "MK"), _city("zurich", "CH"), _city("nowhere", "ZZ")]
    monkeypatch.setattr(
        "preparation.location_data.get", lambda url: _FakeResponse(payload)
    )

    cities = fetch_cities()
    # Every supported country passes by default; the unsupported "ZZ" is dropped.
    assert {city["countryCode"] for city in cities} == {"MK", "CH"}
