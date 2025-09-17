# Gunicorn server configuration
bind = "127.0.0.1:8001"
workers = 4
worker_class = "sync"
reload = True


def post_fork(server, worker):
    """Gunicorn hook that is called after a new worker process is started."""
    from tracing import setup_tracing

    setup_tracing()
