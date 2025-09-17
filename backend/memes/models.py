import os
import uuid
from django.db import models
from django.urls import reverse


class Meme(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image_url = models.URLField()
    top_text = models.CharField(max_length=255, blank=True)
    bottom_text = models.CharField(max_length=255, blank=True)
    generated_image = models.ImageField(upload_to="memes/")
    created_at = models.DateTimeField(auto_now_add=True)

    def get_image_url(self):
        # Generate relative URL
        relative_url = reverse("memes:serve_meme", kwargs={"meme_id": self.id})

        # In Codespaces, return absolute URL with the correct domain
        if os.environ.get("CODESPACE_NAME"):
            codespace_name = os.environ.get("CODESPACE_NAME")
            return f"https://{codespace_name}-8001.app.github.dev{relative_url}"

        # For local development, return relative URL
        return relative_url

    def __str__(self):
        return f"Meme {self.id} - {self.top_text[:20]}..."
