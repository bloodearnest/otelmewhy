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

import argparse
import asyncio
import html
import json
import logging
import os
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
    meme_img_pattern = (
        r'<img[^>]*class=["\'][^"\']*meme-image[^"\']*["\'][^>]*src=["\']([^"\']+)["\']'
    )
    match = re.search(meme_img_pattern, html_content)
    if match:
        return match.group(1)

    # Look for any img tags with /images/ URLs
    img_pattern = r'<img[^>]*src=["\']([^"\']*/?images/[^"\']*\.[^"\']*)["\']'
    match = re.search(img_pattern, html_content)
    if match:
        return match.group(1)

    # Look for img tags with backend URLs (localhost or Codespaces)
    backend_img_pattern = (
        r'<img[^>]*src=["\']([^"\']*(?:127\.0\.0\.1:8001|app\.github\.dev)[^"\']*)["\']'
    )
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


def extract_error_from_html(html_content):
    """Extract error messages from <div class="error"> elements"""
    error_pattern = r'<div[^>]*class=["\'][^"\']*error[^"\']*["\'][^>]*>(.*?)</div>'
    matches = re.findall(error_pattern, html_content, re.DOTALL | re.IGNORECASE)
    if matches:
        # Clean up HTML tags and return joined errors
        errors = []
        for match in matches:
            # Remove HTML tags and clean whitespace
            clean_error = re.sub(r"<[^>]+>", "", match).strip()
            # HTML decode the error message
            clean_error = html.unescape(clean_error)
            if clean_error:
                errors.append(clean_error)
        return "; ".join(errors) if errors else "Error div found but no content"
    return None


async def test_meme_creation_async(semaphore, base_url, meme_data, index):
    """Test creating a single meme through the web interface (async version)"""
    async with semaphore:  # Limit concurrent requests
        try:
            # Disable httpx logging for this test
            logging.getLogger("httpx").setLevel(logging.WARNING)

            # Create a new client for each test
            async with httpx.AsyncClient(
                timeout=10.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
            ) as client:
                # POST the meme data directly (no CSRF token needed)
                form_data = {
                    "image_url": meme_data["image_url"],
                    "top_text": meme_data["top_text"],
                    "bottom_text": meme_data["bottom_text"],
                }

                # Follow redirects to get the success page
                create_response = await client.post(
                    base_url, data=form_data, follow_redirects=True
                )

                # Check for HTTP errors and print debug info if needed
                if create_response.status_code != 200:
                    error_msg = extract_error_from_html(create_response.text)
                    print(
                        f"❌ Test {index + 1}: {meme_data['top_text'][:30]}... -> HTTP {create_response.status_code}"
                    )
                    if error_msg:
                        print(f"   Error: {error_msg}")
                    else:
                        print(f"   Response headers: {dict(create_response.headers)}")
                        print(f"   Response text: {create_response.text}")
                    return False

                # Extract meme image URL from response (but don't fetch the image)
                try:
                    meme_image_url = extract_meme_url_from_html(create_response.text)
                except ValueError as e:
                    # If we can't find it in HTML, maybe it's a JSON response
                    try:
                        response_data = create_response.json()
                        if "meme_url" in response_data:
                            meme_image_url = response_data["meme_url"]
                        else:
                            error_msg = extract_error_from_html(create_response.text)
                            print(
                                f"❌ Test {index + 1}: {meme_data['top_text'][:30]}... -> ERROR: {e}"
                            )
                            if error_msg:
                                print(f"   Error: {error_msg}")
                            else:
                                print(
                                    f"   Response status: {create_response.status_code}"
                                )
                                print(f"   Response text: {create_response.text}")
                            return False
                    except json.JSONDecodeError:
                        error_msg = extract_error_from_html(create_response.text)
                        print(
                            f"❌ Test {index + 1}: {meme_data['top_text'][:30]}... -> ERROR: {e}"
                        )
                        if error_msg:
                            print(f"   Error: {error_msg}")
                        else:
                            print(f"   Response status: {create_response.status_code}")
                            print(f"   Response text: {create_response.text}")
                        return False

                # Success - print one line summary (no image fetch)
                print(
                    f"✅ Test {index + 1}: {meme_data['top_text'][:30]}... -> {meme_image_url}"
                )
                return True

        except httpx.HTTPStatusError as e:
            error_msg = extract_error_from_html(e.response.text)
            print(
                f"❌ Test {index + 1}: {meme_data['top_text'][:30]}... -> HTTP {e.response.status_code}"
            )
            if error_msg:
                print(f"   Error: {error_msg}")
            else:
                print(f"   Response headers: {dict(e.response.headers)}")
                print(f"   Response text: {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ Test {index + 1}: {meme_data['top_text'][:30]}... -> ERROR: {e}")
            return False


async def run_parallel_tests(test_data, frontend_url, num_tests):
    """Run all tests in parallel with limited concurrency"""
    # Create test list by randomly selecting from test data
    expanded_tests = []
    for _ in range(num_tests):
        meme_data = random.choice(test_data)
        expanded_tests.append(meme_data)

    print(
        f"Running {len(expanded_tests)} tests randomly drawn from {len(test_data)} memes"
    )
    print("Limited to 5 concurrent requests")
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Meme Generator System Test")
    parser.add_argument(
        "-n",
        "--num-tests",
        type=int,
        default=64,
        help="Number of test requests to generate (default: 64)",
    )
    args = parser.parse_args()

    print("=== Meme Generator System Test ===")

    # Configuration - auto-detect Codespaces environment
    if os.environ.get("CODESPACE_NAME"):
        # In GitHub Codespaces, use the forwarded URL format
        codespace_name = os.environ.get("CODESPACE_NAME")
        frontend_url = f"https://{codespace_name}-8000.app.github.dev"
        print(f"Detected Codespaces environment: {codespace_name}")
    else:
        # Local development
        frontend_url = "http://127.0.0.1:8000"
        print("Using local development URLs")

    # Load test data
    try:
        test_data = load_test_data()
        print(f"Loaded {len(test_data)} unique memes")
    except Exception as e:
        print(f"Error loading test data: {e}")
        sys.exit(1)

    # Run tests in parallel
    start_time = time.time()
    passed, total = asyncio.run(
        run_parallel_tests(test_data, frontend_url, args.num_tests)
    )
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
