from json import loads

from flask import url_for
from flask_testing import TestCase

from src.api.app import app


class TestAPI(TestCase):
    def create_app(self):
        app.config["TESTING"] = True
        return app

    # The seeded processed frame (tests/conftest.py) holds a single row at
    # 1704067200. The history endpoints default to the last seven days, so that row is
    # never in range and `data` comes back empty -- which is why asserting the status
    # alone said nothing about the data path. This pins the envelope; the test below
    # asks for the window the seed is actually in and pins the row itself.
    SEEDED_TIME = 1704067200
    SENSOR_POSITION = (41.99249998, 21.423611)

    def _assert_history_payload(self, response):
        payload = loads(response.data)
        self.assertIsInstance(payload, dict)
        self.assertIn("data", payload)
        self.assertIsInstance(payload["data"], list)
        # Echoed back the right way round: a swapped pair is a classic defect here and
        # the status code cannot see it.
        latitude, longitude = self.SENSOR_POSITION
        self.assertAlmostEqual(latitude, payload["latitude"])
        self.assertAlmostEqual(longitude, payload["longitude"])

    def _assert_pollutants_payload(self, response):
        # The list is derived from the columns of the seeded pollution frame, so
        # asserting its contents is what proves the endpoint read the data at all.
        pollutants = loads(response.data)
        self.assertIsInstance(pollutants, list)
        self.assertEqual(
            ["co", "no2", "o3", "pm10", "pm2_5", "so2"],
            sorted(pollutant["value"] for pollutant in pollutants),
        )
        for pollutant in pollutants:
            self.assertTrue(pollutant["name"])

    def test_get_cities(self):
        response = self.client.get(url_for("cities.cities"))
        self.assertEqual(response.status_code, 200)
        # A 200 carrying a malformed or empty list used to pass here. The seeded
        # fixture is skopje/MK, so the collection is pinned by content, not only shape.
        cities = loads(response.data)
        self.assertIsInstance(cities, list)
        self.assertTrue(cities)
        self.assertIn("skopje", [city["cityName"] for city in cities])
        self.assertEqual("MK", cities[0]["countryCode"])

    def test_get_city(self):
        city_name = "skopje"
        response = self.client.get(url_for("cities.cities_name", city_name=city_name))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)["cityName"], city_name)

    def test_get_countries(self):
        response = self.client.get(url_for("countries.countries"))
        self.assertEqual(response.status_code, 200)
        countries = loads(response.data)
        self.assertIsInstance(countries, list)
        self.assertTrue(countries)
        self.assertIn("MK", [country["countryCode"] for country in countries])

    def test_get_country(self):
        country_code = "MK"
        response = self.client.get(
            url_for("countries.countries_code", country_code=country_code)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)["countryCode"], country_code)

    def test_get_city_sensor_history(self):
        city_name = "skopje"
        sensor_id = "1000"
        data_type = "weather"
        response = self.client.get(
            url_for(
                "history.city_sensor",
                city_name=city_name,
                sensor_id=sensor_id,
                data_type=data_type,
            )
        )
        self.assertEqual(response.status_code, 200)
        self._assert_history_payload(response)
        data_type = "pollution"
        response = self.client.get(
            url_for(
                "history.city_sensor",
                city_name=city_name,
                sensor_id=sensor_id,
                data_type=data_type,
            )
        )
        self.assertEqual(response.status_code, 200)
        self._assert_history_payload(response)

    def test_get_coordinates_history(self):
        latitude = 41.99249998
        longitude = 21.4236110
        data_type = "weather"
        response = self.client.get(
            url_for(
                "history.coordinates",
                latitude=latitude,
                longitude=longitude,
                data_type=data_type,
            )
        )
        self.assertEqual(response.status_code, 200)
        self._assert_history_payload(response)
        data_type = "pollution"
        response = self.client.get(
            url_for(
                "history.coordinates",
                latitude=latitude,
                longitude=longitude,
                data_type=data_type,
            )
        )
        self.assertEqual(response.status_code, 200)
        self._assert_history_payload(response)

    def test_get_city_sensor_pollutants(self):
        city_name = "skopje"
        sensor_id = "1000"
        response = self.client.get(
            url_for("pollutants.city_sensor", city_name=city_name, sensor_id=sensor_id)
        )
        self.assertEqual(response.status_code, 200)
        self._assert_pollutants_payload(response)

    def test_get_coordinates_pollutants(self):
        latitude = 41.99249998
        longitude = 21.4236110
        response = self.client.get(
            url_for("pollutants.coordinates", latitude=latitude, longitude=longitude)
        )
        self.assertEqual(response.status_code, 200)
        self._assert_pollutants_payload(response)

    def test_get_city_sensor_history_returns_the_seeded_rows(self):
        # Every other history test uses the default window -- the last seven days --
        # which the seeded row (2024-01-01) is not in, so they all assert 200 over an
        # empty `data`. Asking for the window the seed IS in is what exercises the read
        # path: a history endpoint that returned nothing, or dropped a column, or served
        # another sensor's frame, is invisible to the other tests and fails here.
        response = self.client.get(
            url_for(
                "history.city_sensor",
                city_name="skopje",
                sensor_id="1000",
                data_type="weather",
                start_time=self.SEEDED_TIME - 3600,
                end_time=self.SEEDED_TIME + 3600,
            )
        )

        self.assertEqual(response.status_code, 200)
        payload = loads(response.data)
        self.assertEqual(1, len(payload["data"]))
        row = payload["data"][0]
        self.assertEqual(self.SEEDED_TIME, row["time"])
        self.assertAlmostEqual(7.5, row["temperature"])
        self.assertAlmostEqual(60.0, row["humidity"])
        self.assertAlmostEqual(1013.0, row["pressure"])

    def test_get_city_sensors(self):
        city_name = "skopje"
        response = self.client.get(url_for("sensors.sensors_all", city_name=city_name))
        self.assertEqual(response.status_code, 200)

    def test_get_city_sensor(self):
        city_name = "skopje"
        sensor_id = "1000"
        response = self.client.get(
            url_for("sensors.sensors_id", city_name=city_name, sensor_id=sensor_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)["sensorId"], sensor_id)
