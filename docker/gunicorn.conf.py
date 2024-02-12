from multiprocessing import cpu_count

wsgi_app = "app:app"
disable_redirect_access_to_syslog = True

chdir = "/app/src/api"
pidfile = "/run/.pid"
bind = ["unix:/run/gunicorn.socket"]
workers = cpu_count() * 2 + 1
threads = 2
timeout = 0
