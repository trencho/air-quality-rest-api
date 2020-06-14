from os import environ

from flask_pymongo import PyMongo

from definitions import mongo_db_host_env_value, mongo_db_name_env_value, mongo_db_user_name_env_value, \
    mongo_db_user_pass_env_value

mongo = PyMongo()


def configure_database(app):
    app.config['MONGO_URI'] = ('mongodb+srv://' + environ.get(mongo_db_user_name_env_value) + ':'
                               + environ.get(mongo_db_user_pass_env_value) + '@' + environ.get(mongo_db_host_env_value)
                               + '/' + environ.get(mongo_db_name_env_value) + '?retryWrites=true&w=majority')
    mongo.init_app(app)
