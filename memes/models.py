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
        return reverse("memes:serve_meme", kwargs={"meme_id": self.id})

    def __str__(self):
        return f"Meme {self.id} - {self.top_text[:20]}..."
