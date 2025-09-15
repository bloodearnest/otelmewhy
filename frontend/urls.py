"""
URL configuration for frontend project.

The frontend web UI service for meme generation.
"""

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
import views

urlpatterns = [
    path("", views.meme_generator, name="meme_generator"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
