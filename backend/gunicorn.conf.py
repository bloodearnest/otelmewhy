# Gunicorn server configuration
from dotenv import load_dotenv
from tracing import setup_tracing
import logging

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m',      # Reset
        'BACKEND': '\033[34m',   # Blue
    }

    def format(self, record):
        # Add color to log level
        level_color = self.COLORS.get(record.levelname, '')
        backend_color = self.COLORS['BACKEND']
        reset = self.COLORS['RESET']

        # Customize the format with colors
        original_format = self._style._fmt
        colored_format = f"%(asctime)s [{level_color}%(levelname)s{reset}] [{backend_color}BACKEND{reset} ] %(message)s"
        self._style._fmt = colored_format

        formatted = super().format(record)
        self._style._fmt = original_format  # Reset format
        return formatted

# use the default synchronous worker
workers = 4
worker_class = "sync"
# reload on code chagnes
reload = True
# reload if the env vars change. Note that we need the load_dotenv call below
# for this to actually re-load them in gunicorn workers.
reload_extra_files = [".env", "../.env"]

# Custom log format to identify this as backend
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": ColoredFormatter,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "colored",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "gunicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Custom access log format without timestamp (since it's in the main log format)
access_log_format = '%(m)s %(U)s %(s)s %(B)s'


def post_fork(server, worker):
    """Gunicorn hook that is called after a new worker process is started."""
    # Reload .env file to pick up any changes - this is a convenience for the workshop
    load_dotenv(".env", override=True)
    # setup our tracing in the new worker process
    setup_tracing(server, worker)
