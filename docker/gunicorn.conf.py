from logging import basicConfig, getLogger, INFO
from multiprocessing import cpu_count

wsgi_app = "app:app"
disable_redirect_access_to_syslog = True

preload_app = True
chdir = "/app/src/api"
# /run is root-owned and the process is unprivileged, so the pid file and the socket nginx proxies
# to both live under /tmp. nginx's proxy_pass in docker/nginx.conf points at the same path.
pidfile = "/tmp/gunicorn.pid"
bind = ["unix:/tmp/gunicorn.socket"]
workers = cpu_count() * 2 + 1
threads = 4
max_requests = 500
max_requests_jitter = 50

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.info("Gunicorn configured successfully")
