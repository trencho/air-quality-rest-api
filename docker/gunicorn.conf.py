from logging import basicConfig, getLogger, INFO
from multiprocessing import cpu_count

wsgi_app = "app:app"
disable_redirect_access_to_syslog = True

preload_app = True
chdir = "/app/src/api"
pidfile = "/run/.pid"
bind = ["unix:/run/gunicorn.socket"]
workers = cpu_count() * 2 + 1
threads = 4
max_requests = 500
max_requests_jitter = 50

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.info("Gunicorn configured successfully")
