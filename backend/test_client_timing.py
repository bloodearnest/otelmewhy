import time
from memes.utils import httpx_client


def test_url(url):
    """Test a single HTTP request and report timing using memes.utils client."""
    print(f"Testing URL: {url}")

    # Check if patch was applied
    print(f"Client get method: {httpx_client.get.__name__}")
    if hasattr(httpx_client.get, "__name__") and "patched" in httpx_client.get.__name__:
        print("✅ Patch detected")
    else:
        print("⚠️  Patch may not be applied")

    # Warmup request to establish connection (don't measure this)
    print("🔄 Warmup request (establishing connection)...")
    try:
        warmup_response = httpx_client.get(url)
        print(f"   Warmup status: {warmup_response.status_code}")
    except Exception as e:
        print(f"   Warmup failed: {e}")
        return

    # Actual measured request (connection already established)
    print("📊 Measured request (using existing connection)...")
    start_time = time.time()
    try:
        response = httpx_client.get(url)
        end_time = time.time()

        duration = end_time - start_time

        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"📦 Content-Length: {len(response.content)} bytes")

        # Check if this looks like an imgflip delay
        if "imgflip.com" in url:
            if duration > 1.5:
                print("🐌 Artificial delay detected (expected for imgflip.com)")
            else:
                print("⚠️  No artificial delay detected (unexpected for imgflip.com)")
        else:
            if duration > 1.5:
                print(
                    "⚠️  Unexpectedly slow (artificial delay should only apply to imgflip.com)"
                )
            else:
                print("🚀 Fast response (expected for non-imgflip URLs)")

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ Error after {duration:.2f}s: {e}")


def test_fetch_image(url):
    """Test using the actual fetch_image function from memes.utils."""
    from memes.utils import fetch_image

    print(f"Testing fetch_image with URL: {url}")

    # Warmup request to establish connection (don't measure this)
    print("🔄 Warmup fetch_image (establishing connection)...")
    try:
        warmup_image = fetch_image(url)
        print(f"   Warmup image size: {warmup_image.size}")
    except Exception as e:
        print(f"   Warmup failed: {e}")
        return

    # Actual measured request (connection already established)
    print("📊 Measured fetch_image (using existing connection)...")
    start_time = time.time()
    try:
        image = fetch_image(url)
        end_time = time.time()

        duration = end_time - start_time

        print(f"✅ Image loaded successfully")
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"📦 Image size: {image.size}")

        # Check if this looks like an imgflip delay
        if "imgflip.com" in url:
            if duration > 1.5:
                print("🐌 Artificial delay detected (expected for imgflip.com)")
            else:
                print("⚠️  No artificial delay detected (unexpected for imgflip.com)")
        else:
            if duration > 1.5:
                print(
                    "⚠️  Unexpectedly slow (artificial delay should only apply to imgflip.com)"
                )
            else:
                print("🚀 Fast response (expected for non-imgflip URLs)")

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ Error after {duration:.2f}s: {e}")


# Run tests
print("=== Testing imgflip URL (should have delay) ===")
test_url("https://i.imgflip.com/1bij.jpg")

print("\n=== Testing non-imgflip URL (should be fast) ===")
test_url("https://httpbin.org/get")

# Reset connection pool to ensure fresh connections for fetch_image test
print("\n🔄 Resetting connection pool...")
# Close existing connections but keep the client alive
if hasattr(httpx_client, "_transport"):
    httpx_client._transport.close()
print("   Connection pool reset complete")

print("\n=== Testing fetch_image function ===")
test_fetch_image("https://i.imgflip.com/1bij.jpg")
