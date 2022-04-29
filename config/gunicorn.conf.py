wsgi_app = 'app:app'
disable_redirect_access_to_syslog = True
preload_app = True
chdir = '/src/api'
pidfile = '/run/.pid'
uid = 'root'
gid = 'root'
bind = ['unix:/run/gunicorn.socket']
