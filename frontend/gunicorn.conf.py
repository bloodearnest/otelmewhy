# Gunicorn server configuration
bind = "127.0.0.1:8000"
workers = 1
worker_class = "sync"
