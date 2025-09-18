"""
HTTP client configuration with connection pooling and artificial delays.

This module creates a global httpx client and provides patching functionality
for adding artificial delays to imgflip.com requests.
"""

import random
import time
from urllib.parse import urlparse
import httpx

# Patch HTTPTransport.handle_request at the class level BEFORE OpenTelemetry instrumentation
# This is the exact same method that OpenTelemetry wraps
_original_handle_request = httpx.HTTPTransport.handle_request


def _patched_handle_request(self, request):
    """Patched HTTPTransport.handle_request that adds delay for imgflip.com domains."""
    # Check if this is a request to imgflip.com
    if request.url.host and "imgflip.com" in request.url.host:
        delay = random.gammavariate(alpha=2, beta=2)
        print(f"delay: {delay}")
        time.sleep(delay)

    return _original_handle_request(self, request)


# Patch is not applied automatically - call patch_imgflip_delay() to enable

# Global HTTP client with larger connection pool for backend image fetching
httpx_client = httpx.Client(
    timeout=15.0,
    limits=httpx.Limits(
        max_keepalive_connections=50,  # Much larger pool
        max_connections=100,  # Support high concurrency
        keepalive_expiry=60.0,  # Keep connections longer
    ),
    follow_redirects=True,
)


def patch_imgflip_delay():
    """Apply the imgflip delay patch to the httpx client."""
    httpx.HTTPTransport.handle_request = _patched_handle_request
