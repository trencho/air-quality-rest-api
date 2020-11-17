from os import environ

from flask_pymongo import PyMongo

from definitions import mongodb_connection_env, mongodb_db_name_env, mongodb_host_env, mongodb_password_env, \
    mongodb_username_env

mongo = PyMongo()


def configure_database(app):
    app.config['MONGO_URI'] = (
        f'{environ[mongodb_connection_env]}://{environ[mongodb_username_env]}:{environ[mongodb_password_env]}@'
        f'{environ[mongodb_host_env]}/{environ[mongodb_db_name_env]}?retryWrites=true&w=majority'
    )
    mongo.init_app(app)
