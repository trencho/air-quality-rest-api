from os import environ

from flask import Flask
from flask_pymongo import ASCENDING, PyMongo

from definitions import collections, mongo_database, mongo_password, mongo_username, mongodb_connection, \
    mongodb_hostname

mongo = PyMongo()


def configure_database(app: Flask) -> None:
    app.config['MONGO_URI'] = (
        f'{environ[mongodb_connection]}://{environ[mongo_username]}:{environ[mongo_password]}@'
        f'{environ[mongodb_hostname]}/{environ[mongo_database]}?authSource=admin&retryWrites=true&w=majority'
    )
    mongo.init_app(app)
    create_indexes()


def create_indexes():
    mongo.db['cities'].create_index([('cityName', ASCENDING)])
    mongo.db['sensors'].create_index([('sensorId', ASCENDING)])
    mongo.db['predictions'].create_index([('cityName', ASCENDING), ('sensorId', ASCENDING)])
    for collection in collections:
        mongo.db[collection].create_index([('sensorId', ASCENDING)])
