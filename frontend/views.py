import json
import random
import httpx
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.conf import settings
from urllib.parse import urlparse, urljoin
from pathlib import Path


def get_simple_client():
    return httpx.Client(timeout=15.0)


def is_valid_url(url: str) -> bool:
    """Validate that the URL has a proper format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def load_test_data():
    """Load test data from test-data.json"""
    test_data_path = Path(__file__).parent / "test-data.json"
    try:
        with open(test_data_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback to hardcoded default if file not found or invalid
        return [
            {
                "image_url": "https://cdn-useast1.kapwing.com/static/templates/x-x-everywhere-meme-template-full-96173e84.webp",
                "top_text": "SPANS",
                "bottom_text": "SPANS EVERYWHERE",
            }
        ]


def get_random_default_data():
    """Get a random meme from test data for default form values"""
    test_data = load_test_data()
    return random.choice(test_data)


def meme_generator(request: HttpRequest) -> HttpResponse:
    """View for the meme generator form and preview."""
    errors = []
    # Get random default data from test-data.json
    default_form_data = get_random_default_data()
    form_data = default_form_data.copy()
    meme_image_url = None

    if request.method == "POST":
        # Get form data
        image_url = request.POST.get("image_url", "").strip()
        top_text = request.POST.get("top_text", "").strip()
        bottom_text = request.POST.get("bottom_text", "").strip()

        # Store form data for repopulation (overrides defaults)
        form_data = {
            "image_url": image_url,
            "top_text": top_text,
            "bottom_text": bottom_text,
        }

        # Validation
        if not image_url:
            errors.append("Image URL is required.")
        elif not is_valid_url(image_url):
            errors.append("Please enter a valid URL.")

        if len(top_text) > 100:
            errors.append("Top text must be 100 characters or less.")

        if len(bottom_text) > 100:
            errors.append("Bottom text must be 100 characters or less.")

        # If no validation errors, call the memes API
        if not errors:
            try:
                # Prepare API request data
                api_data = {
                    "image_url": image_url,
                    "top_text": top_text,
                    "bottom_text": bottom_text,
                }

                # Make request to backend memes API
                api_url = urljoin(settings.BACKEND_URL, "/api/create/")

                with get_simple_client() as client:
                    response = client.post(
                        api_url,
                        json=api_data,
                        headers={"Content-Type": "application/json"},
                    )

                if response.status_code == 201:
                    # Success - extract meme ID and redirect to GET with query param
                    result = response.json()
                    meme_id = result.get("id")
                    if meme_id:
                        return redirect(f"/?meme_id={meme_id}")
                else:
                    # API returned an error
                    try:
                        error_data = response.json()
                        error_message = error_data.get(
                            "error",
                            f"API request failed with status {response.status_code}",
                        )
                    except json.JSONDecodeError:
                        error_message = (
                            f"API request failed with status {response.status_code}"
                        )
                    errors.append(f"Failed to generate meme: {error_message}")

            except httpx.RequestError as e:
                errors.append(f"Network error: {str(e)}")
            except httpx.TimeoutException:
                errors.append("Request timed out. Please try again.")
            except Exception as e:
                errors.append(f"Unexpected error: {str(e)}")

    elif request.method == "GET":
        # Check for meme_id query parameter
        meme_id = request.GET.get("meme_id")
        if meme_id:
            try:
                # Construct meme image URL directly using the backend URL and meme ID
                meme_image_url = urljoin(settings.BACKEND_URL, f"/images/{meme_id}/")

                # Get meme details to populate form
                api_url = urljoin(settings.BACKEND_URL, f"/api/meme/{meme_id}/")
                with get_simple_client() as client:
                    response = client.get(api_url)

                if response.status_code == 200:
                    result = response.json()
                    form_data = {
                        "image_url": result.get("original_image_url", ""),
                        "top_text": result.get("top_text", ""),
                        "bottom_text": result.get("bottom_text", ""),
                    }
                else:
                    errors.append(
                        f"Could not load meme details (HTTP {response.status_code})"
                    )

            except Exception as e:
                errors.append(f"Error loading meme: {str(e)}")
                meme_image_url = None

    # Get random data for the "Generate Random Meme" form
    random_meme_data = get_random_default_data()

    return render(
        request,
        "frontend/meme_generator.html",
        {
            "errors": errors,
            "form_data": form_data,
            "meme_image_url": meme_image_url,
            "random_meme_data": random_meme_data,
        },
    )
