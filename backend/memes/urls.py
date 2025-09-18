from django.urls import path
from memes import views

app_name = "memes"

urlpatterns = [
    path("", views.health_check, name="health_check"),
    path("api/create/", views.create_meme, name="create_meme"),
    path("api/meme/<uuid:meme_id>/", views.get_meme, name="get_meme"),
    path("images/<uuid:meme_id>/", views.serve_meme, name="serve_meme"),
]
