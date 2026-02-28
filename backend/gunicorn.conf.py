# Gunicorn configuration for blog-jun production
# CPU * 2 + 1 (4 CPU 기준)
workers = 5
worker_class = "gthread"
threads = 2
timeout = 60
max_requests = 1000
max_requests_jitter = 100
preload_app = True
bind = "0.0.0.0:8000"
accesslog = "/app/logs/gunicorn-access.log"
errorlog = "/app/logs/gunicorn-error.log"
loglevel = "info"
