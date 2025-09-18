"""
HTTP client configuration with connection pooling for frontend.

This module creates a global httpx client and provides connection warming functionality.
"""

import httpx
import logging

# Global HTTP client with connection pooling for frontend requests
httpx_client = httpx.Client(
    timeout=15.0,
    limits=httpx.Limits(
        max_keepalive_connections=10,
        max_connections=20,
        keepalive_expiry=120.0,  # 2 minutes to keep connections alive longer
    ),
)


def warm_backend_connection():
    """Make a speculative connection to the backend to warm up the connection pool."""
    try:
        from django.conf import settings

        # Make a quick HEAD request to warm up the connection
        backend_url = settings.BACKEND_URL
        warmup_response = httpx_client.head(f"{backend_url}/", timeout=5.0)

        logger = logging.getLogger("gunicorn.error")
        logger.info(
            f"Warmed up connection to backend (status: {warmup_response.status_code})"
        )

        return True
    except Exception as e:
        logger = logging.getLogger("gunicorn.error")
        logger.warning(f"Failed to warm up backend connection: {e}")
        return False
