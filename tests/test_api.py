from json import loads

from flask import url_for
from flask_testing import TestCase

from src.api.app import app


class TestAPI(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app

    def test_get_cities(self):
        response = self.client.get(url_for("cities.cities"))
        self.assertEqual(response.status_code, 200)

    def test_get_city(self):
        city_name = "skopje"
        response = self.client.get(url_for("cities.cities_name", city_name=city_name))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)["cityName"], city_name)

    def test_get_countries(self):
        response = self.client.get(url_for("countries.countries"))
        self.assertEqual(response.status_code, 200)

    def test_get_country(self):
        country_code = "MK"
        response = self.client.get(url_for("countries.countries_code", country_code=country_code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)["countryCode"], country_code)

    def test_get_city_sensor_history(self):
        city_name = "skopje"
        sensor_id = "1000"
        data_type = "weather"
        response = self.client.get(
            url_for("history.city_sensor", city_name=city_name, sensor_id=sensor_id, data_type=data_type))
        self.assertEqual(response.status_code, 200)
        # TODO: Add additional assertions for the received data
        data_type = "pollution"
        response = self.client.get(
            url_for("history.city_sensor", city_name=city_name, sensor_id=sensor_id, data_type=data_type))
        self.assertEqual(response.status_code, 200)
        # TODO: Add additional assertions for the received data

    def test_get_coordinates_history(self):
        latitude = 41.99249998
        longitude = 21.4236110
        data_type = "weather"
        response = self.client.get(
            url_for("history.coordinates", latitude=latitude, longitude=longitude, data_type=data_type))
        self.assertEqual(response.status_code, 200)
        # TODO: Add additional assertions for the received data
        data_type = "pollution"
        response = self.client.get(
            url_for("history.coordinates", latitude=latitude, longitude=longitude, data_type=data_type))
        self.assertEqual(response.status_code, 200)
        # TODO: Add additional assertions for the received data

    def test_get_city_sensor_pollutants(self):
        city_name = "skopje"
        sensor_id = "1000"
        response = self.client.get(url_for("pollutants.city_sensor", city_name=city_name, sensor_id=sensor_id))
        self.assertEqual(response.status_code, 200)
        # TODO: Add additional assertions for the received data

    def test_get_coordinates_pollutants(self):
        latitude = 41.99249998
        longitude = 21.4236110
        response = self.client.get(url_for("pollutants.coordinates", latitude=latitude, longitude=longitude))
        self.assertEqual(response.status_code, 200)
        # TODO: Add additional assertions for the received data

    def test_get_city_sensors(self):
        city_name = "skopje"
        response = self.client.get(url_for("sensors.sensors_all", city_name=city_name))
        self.assertEqual(response.status_code, 200)

    def test_get_city_sensor(self):
        city_name = "skopje"
        sensor_id = "1000"
        response = self.client.get(url_for("sensors.sensors_id", city_name=city_name, sensor_id=sensor_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)["sensorId"], sensor_id)
