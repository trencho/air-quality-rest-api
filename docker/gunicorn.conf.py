from multiprocessing import cpu_count
from os import environ

from api.config.schedule import scheduler
from definitions import USER_GID, USER_ID

wsgi_app = "app:app"
disable_redirect_access_to_syslog = True


def on_starting(server):
    scheduler.start()


preload_app = True
chdir = "/app/src/api"
pidfile = "/run/.pid"
uid = environ[USER_ID]
gid = environ[USER_GID]
bind = ["unix:/run/gunicorn.socket"]
workers = cpu_count() * 2 + 1
threads = 2
timeout = 0
