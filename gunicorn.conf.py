bind = "0.0.0.0:8000"
workers = 3
keep_alive = 75
timeout = 120
worker_class = "sync"

accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)s'

preload_app = True

def post_fork(server, worker):
    from django.db import connections
    for conn in connections.all():
        conn.close()
