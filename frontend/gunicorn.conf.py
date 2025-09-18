# Gunicorn server configuration
from dotenv import load_dotenv
from tracing import setup_tracing

bind = "127.0.0.1:8000"
# use the default synchronous worker
workers = 4
worker_class = "sync"
# reload on code chagnes
reload = True
# reload if the env vars change. Note that we need the load_dotenv call below
# for this to actually re-load them in gunicorn workers.
reload_extra_files = [".env", "../.env"]


def post_fork(server, worker):
    """Gunicorn hook that is called after a new worker process is started."""
    # Reload .env file to pick up any changes - this is a convenience for the workshop
    load_dotenv(".env", override=True)
    # setup our tracing in the new worker process
    setup_tracing(server, worker)
