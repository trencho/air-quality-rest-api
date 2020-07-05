from os import environ

from flask_pymongo import PyMongo

from definitions import mongodb_host_env_value, mongodb_name_env_value, mongodb_user_name_env_value, \
    mongodb_user_pass_env_value

mongo = PyMongo()


def configure_database(app):
    app.config['MONGO_URI'] = ('mongodb+srv://' + environ.get(mongodb_user_name_env_value) + ':'
                               + environ.get(mongodb_user_pass_env_value) + '@' + environ.get(mongodb_host_env_value)
                               + '/' + environ.get(mongodb_name_env_value) + '?retryWrites=true&w=majority')
    mongo.init_app(app)
