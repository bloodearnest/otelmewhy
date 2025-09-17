import json
import httpx
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.conf import settings
from urllib.parse import urlparse, urljoin


def is_valid_url(url: str) -> bool:
    """Validate that the URL has a proper format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def meme_generator(request: HttpRequest) -> HttpResponse:
    """View for the meme generator form and preview."""
    errors = []
    # Default test data from memes API tests
    default_form_data = {
        "image_url": "https://cdn-useast1.kapwing.com/static/templates/x-x-everywhere-meme-template-full-96173e84.webp",
        "top_text": "SPANS",
        "bottom_text": "SPANS EVERYWHERE",
    }
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

                with httpx.Client() as client:
                    response = client.post(
                        api_url,
                        json=api_data,
                        headers={"Content-Type": "application/json"},
                        timeout=30.0,
                    )

                if response.status_code == 201:
                    # Success - get the meme image URL
                    result = response.json()
                    meme_image_url = result.get("image_url")

                    # Convert relative URLs to absolute URLs using the backend URL
                    if meme_image_url and meme_image_url.startswith("/"):
                        meme_image_url = urljoin(settings.BACKEND_URL, meme_image_url)
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

    return render(
        request,
        "frontend/meme_generator.html",
        {
            "errors": errors,
            "form_data": form_data,
            "meme_image_url": meme_image_url,
        },
    )
