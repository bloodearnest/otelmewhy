import json
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.conf import settings
import os

from memes.models import Meme
from memes.utils import generate_meme


def health_check(request):
    """Basic health check view that returns 'OK'."""
    return HttpResponse("OK")


@csrf_exempt
@require_http_methods(["POST"])
def create_meme(request):
    """JSON API endpoint to create a meme."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    image_url = data.get("image_url")
    top_text = data.get("top_text", "")
    bottom_text = data.get("bottom_text", "")

    if not image_url:
        return JsonResponse({"error": "image_url is required"}, status=400)

    try:
        # Generate the meme image
        meme_file = generate_meme(image_url, top_text, bottom_text)

        # Create and save the meme record
        meme = Meme.objects.create(
            image_url=image_url,
            top_text=top_text,
            bottom_text=bottom_text,
            generated_image=meme_file,
        )

        return JsonResponse(
            {
                "id": str(meme.id),
                "image_url": request.build_absolute_uri(meme.get_image_url()),
                "created_at": meme.created_at.isoformat(),
            },
            status=201,
        )

    except Exception as e:
        return JsonResponse({"error": f"Failed to generate meme: {str(e)}"}, status=500)


def serve_meme(request, meme_id):
    """Serve the generated meme image."""
    meme = get_object_or_404(Meme, id=meme_id)

    if not meme.generated_image:
        raise Http404("Image not found")

    try:
        with open(meme.generated_image.path, "rb") as f:
            response = HttpResponse(f.read(), content_type="image/png")
            response["Content-Disposition"] = f'inline; filename="meme_{meme.id}.png"'
            return response
    except FileNotFoundError:
        raise Http404("Image file not found")
