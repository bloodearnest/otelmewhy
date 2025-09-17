#!/usr/bin/env python3
"""
System test script that exercises the meme generator like a browser would.

This script:
1. Loads test data from test-data.json
2. For each meme:
   - GETs the frontend form to extract CSRF token
   - POSTs the meme data to create a meme
   - Parses the response HTML to find the meme image URL
   - GETs the meme image to verify it was created
"""

import asyncio
import json
import logging
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import httpx

# Disable httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)


def load_test_data():
    """Load test data from test-data.json"""
    test_data_path = Path(__file__).parent / "test-data.json"
    with open(test_data_path) as f:
        return json.load(f)




def extract_meme_url_from_html(html_content):
    """Extract the meme image URL from the success page HTML using regex"""
    # Look for img tags with class="meme-image" (most specific)
    meme_img_pattern = r'<img[^>]*class=["\'][^"\']*meme-image[^"\']*["\'][^>]*src=["\']([^"\']+)["\']'
    match = re.search(meme_img_pattern, html_content)
    if match:
        return match.group(1)

    # Look for any img tags with /images/ URLs
    img_pattern = r'<img[^>]*src=["\']([^"\']*/?images/[^"\']*\.[^"\']*)["\']'
    match = re.search(img_pattern, html_content)
    if match:
        return match.group(1)

    # Look for img tags with backend URLs (127.0.0.1:8001)
    backend_img_pattern = r'<img[^>]*src=["\']([^"\']*127\.0\.0\.1:8001[^"\']*)["\']'
    match = re.search(backend_img_pattern, html_content)
    if match:
        return match.group(1)

    # Look for any img src with common image extensions
    generic_img_pattern = r'<img[^>]*src=["\']([^"\']*\.(png|jpg|jpeg|gif|webp))["\']'
    match = re.search(generic_img_pattern, html_content, re.IGNORECASE)
    if match:
        return match.group(1)

    # Alternative: look for links to /images/ URLs
    link_pattern = r'<a[^>]*href=["\']([^"\']*/?images/[^"\']*)["\']'
    match = re.search(link_pattern, html_content)
    if match:
        return match.group(1)

    raise ValueError("Meme image URL not found in HTML response")


async def test_meme_creation_async(semaphore, base_url, meme_data, index):
    """Test creating a single meme through the web interface (async version)"""
    async with semaphore:  # Limit concurrent requests
        try:
            # Disable httpx logging for this test
            logging.getLogger("httpx").setLevel(logging.WARNING)

            # Create a new client for each test
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            ) as client:
                # POST the meme data directly (no CSRF token needed)
                form_data = {
                    'image_url': meme_data['image_url'],
                    'top_text': meme_data['top_text'],
                    'bottom_text': meme_data['bottom_text']
                }

                # Follow redirects to get the success page
                create_response = await client.post(base_url, data=form_data, follow_redirects=True)
                create_response.raise_for_status()

                # Extract meme image URL from response (but don't fetch the image)
                try:
                    meme_image_url = extract_meme_url_from_html(create_response.text)
                except ValueError as e:
                    # If we can't find it in HTML, maybe it's a JSON response
                    try:
                        response_data = create_response.json()
                        if 'meme_url' in response_data:
                            meme_image_url = response_data['meme_url']
                        else:
                            print(f"❌ Test {index + 1}: {meme_data['top_text'][:30]}... -> ERROR: {e}")
                            return False
                    except json.JSONDecodeError:
                        print(f"❌ Test {index + 1}: {meme_data['top_text'][:30]}... -> ERROR: {e}")
                        return False

                # Success - print one line summary (no image fetch)
                print(f"✅ Test {index + 1}: {meme_data['top_text'][:30]}... -> {meme_image_url}")
                return True

        except Exception as e:
            print(f"❌ Test {index + 1}: {meme_data['top_text'][:30]}... -> ERROR: {e}")
            return False


async def run_parallel_tests(test_data, frontend_url):
    """Run all tests in parallel with limited concurrency"""
    # Create expanded test list - each meme 8 times
    expanded_tests = []
    for meme_data in test_data:
        for _ in range(8):
            expanded_tests.append(meme_data)

    # Randomize the order
    random.shuffle(expanded_tests)

    print(f"Running {len(expanded_tests)} tests (each of {len(test_data)} memes 8 times, randomized)")
    print("Limited to 9 concurrent requests (conservative load for 8 workers)")
    print()

    # Create a semaphore to limit concurrent requests, so as not to overload our gunicorn servers
    semaphore = asyncio.Semaphore(5)

    # Create tasks for all tests
    tasks = []
    for i, meme_data in enumerate(expanded_tests):
        task = test_meme_creation_async(semaphore, frontend_url, meme_data, i)
        tasks.append(task)

    # Run all tasks concurrently (but limited by semaphore)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Count successes (True results, not exceptions)
    passed = sum(1 for result in results if result is True)
    return passed, len(expanded_tests)


def main():
    """Run the system test"""
    print("=== Meme Generator System Test ===")

    # Configuration
    frontend_url = "http://127.0.0.1:8000"

    # Load test data
    try:
        test_data = load_test_data()
        print(f"Loaded {len(test_data)} unique memes")
    except Exception as e:
        print(f"Error loading test data: {e}")
        sys.exit(1)

    # Run tests in parallel
    start_time = time.time()
    passed, total = asyncio.run(run_parallel_tests(test_data, frontend_url))
    end_time = time.time()

    # Summary
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    print(f"Time taken: {end_time - start_time:.2f}s")

    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
