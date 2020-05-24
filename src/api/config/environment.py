import os

from definitions import environment_variables


def check_environment_variables():
    for environment_variable in environment_variables:
        env = os.environ.get(environment_variable)
        if env is None:
            print('The environment variable \'' + environment_variable + '\' is not set')
            exit(-1)
