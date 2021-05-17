from os import environ

from flask_pymongo import PyMongo

from definitions import mongo_database, mongo_password, mongo_username, mongodb_connection, mongodb_hostname

mongo = PyMongo()


def configure_database(app):
    app.config['MONGO_URI'] = (
        f'{environ[mongodb_connection]}://{environ[mongo_username]}:{environ[mongo_password]}@'
        f'{environ[mongodb_hostname]}/{environ[mongo_database]}?authSource=admin&retryWrites=true&w=majority'
    )
    mongo.init_app(app)
