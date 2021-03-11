from os import environ

from flask_pymongo import PyMongo

from definitions import mongodb_connection, mongodb_db_name, mongodb_host, mongodb_password, mongodb_username

mongo = PyMongo()


def configure_database(app):
    app.config['MONGO_URI'] = (
        f'{environ[mongodb_connection]}://{environ[mongodb_username]}:{environ[mongodb_password]}@'
        f'{environ[mongodb_host]}/{environ[mongodb_db_name]}?retryWrites=true&w=majority'
    )
    mongo.init_app(app)
