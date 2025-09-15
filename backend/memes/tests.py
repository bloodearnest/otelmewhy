import json
import uuid
from io import BytesIO

import pytest
from django.test import Client, override_settings
from django.urls import reverse
from PIL import Image

from memes.models import Meme


# Real Buzz Lightyear "X, X Everywhere" meme template from Kapwing
BUZZ_LIGHTYEAR_URL = "https://cdn-useast1.kapwing.com/static/templates/x-x-everywhere-meme-template-full-96173e84.webp"


@pytest.fixture
def client():
    return Client()


@override_settings(MEDIA_ROOT="/tmp/test_media")
def test_full_integration_workflow_with_buzz_lightyear(client):
    """Full integration test: create Buzz Lightyear meme then fetch the image."""
    # Step 1: Create a meme via API using real Buzz Lightyear image
    meme_data = {
        "image_url": BUZZ_LIGHTYEAR_URL,
        "top_text": "SPANS",
        "bottom_text": "SPANS EVERYWHERE",
    }

    create_response = client.post(
        reverse("memes:create_meme"),
        data=json.dumps(meme_data),
        content_type="application/json",
    )

    assert create_response.status_code == 201
    response_data = create_response.json()

    # Step 2: Extract the meme ID
    meme_id = response_data["id"]
    assert uuid.UUID(meme_id)  # Verify it's a valid UUID

    # Step 3: Fetch the generated image
    image_response = client.get(
        reverse("memes:serve_meme", kwargs={"meme_id": meme_id})
    )

    assert image_response.status_code == 200
    assert image_response["Content-Type"] == "image/png"

    # Step 4: Verify the image is properly generated
    generated_image = Image.open(BytesIO(image_response.content))
    assert generated_image.format == "PNG"
    assert generated_image.size[0] > 200
    assert generated_image.size[1] > 200

    # Verify database record contains correct data
    meme = Meme.objects.get(id=meme_id)
    assert meme.top_text == "SPANS"
    assert meme.bottom_text == "SPANS EVERYWHERE"
    assert meme.image_url == BUZZ_LIGHTYEAR_URL
    assert meme.generated_image.name.endswith(".png")

    # Verify the actual file exists and has content
    assert meme.generated_image.size > 0
