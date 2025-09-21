import io
import os
import random
import re
import time
from urllib.parse import urlparse
import httpx
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.conf import settings
from client import httpx_client
from opentelemetry import trace
from functools import wraps

tracer = trace.get_tracer("memes.generate")


def span_decorator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with tracer.start_as_current_span(f.__name__):
            return f(*args, **kwargs)

    return wrapper


def load_impact_font(size):
    """Load Impact font with fallbacks, centralized font loading utility."""
    try:
        # Try unicode Impact font first for emoji support
        impact_path = os.path.join(settings.MEDIA_ROOT, "fonts", "unicode.impact.ttf")
        if not os.path.exists(impact_path):
            impact_path = os.path.join(settings.MEDIA_ROOT, "fonts", "impact.ttf")
        if not os.path.exists(impact_path):
            # Fallback to project media directory
            impact_path = "/home/wavy/otelmewhy/media/fonts/unicode.impact.ttf"
            if not os.path.exists(impact_path):
                impact_path = "/home/wavy/otelmewhy/media/fonts/impact.ttf"
        return ImageFont.truetype(impact_path, size)
    except (OSError, IOError):
        try:
            # Try to use a bolder system font
            return ImageFont.truetype(
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", size
            )
        except (OSError, IOError):
            try:
                return ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVu-Sans-Bold.ttf", size
                )
            except (OSError, IOError):
                return ImageFont.load_default()




def fetch_image(image_url):
    """Fetch image from URL and return PIL Image object."""
    response = httpx_client.get(image_url)
    response.raise_for_status()
    content = io.BytesIO(response.content)
    return Image.open(content)


def calculate_font_size(text, image_width, image_height):
    """Calculate optimal font size based on text length and image dimensions."""
    if not text:
        return 40

    max_font_size = min(image_width // 2, image_height // 3)

    test_font = load_impact_font(max_font_size)
    if test_font == ImageFont.load_default():
        max_font_size = 40

    margin_percent = 0.1
    margin = image_width * margin_percent
    available_width = image_width - (2 * margin)

    font_size = max_font_size
    while font_size > 20:
        try:
            current_font = load_impact_font(font_size)

            bbox = current_font.getbbox(text.upper())
            text_width = bbox[2] - bbox[0]

            if text_width <= available_width:
                return font_size

            font_size = int(font_size * 0.9)
        except Exception as e:
            break

    return max(font_size, 20)


def draw_text_with_outline(
    draw,
    text,
    position,
    font,
    fill_color="white",
    outline_color="black",
    outline_width=2,
):
    """Draw text with outline."""
    x, y = position
    text = text.upper()

    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text(position, text, font=font, fill=fill_color)


def generate_meme(image_url, top_text="", bottom_text=""):
    """Generate a meme by adding text to an image."""
    base_image = fetch_image(image_url)

    if base_image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", base_image.size, (255, 255, 255))
        background.paste(
            base_image,
            mask=base_image.split()[-1] if base_image.mode == "RGBA" else None,
        )
        base_image = background
    elif base_image.mode != "RGB":
        base_image = base_image.convert("RGB")

    draw = ImageDraw.Draw(base_image)

    width, height = base_image.size

    top_font_size = calculate_font_size(top_text, width, height)
    bottom_font_size = calculate_font_size(bottom_text, width, height)

    font_size = (
        min(top_font_size, bottom_font_size)
        if top_text and bottom_text
        else max(top_font_size, bottom_font_size, 40)
    )

    font = load_impact_font(font_size)

    if top_text:
        bbox = draw.textbbox((0, 0), top_text.upper(), font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) // 2
        top_margin_percent = 0.05
        top_margin = max(int(height * top_margin_percent), 20)
        y = top_margin

        outline_width = max(font_size // 20, 3)
        draw_text_with_outline(
            draw, top_text.upper(), (x, y), font, outline_width=outline_width
        )

    if bottom_text:
        bbox = draw.textbbox((0, 0), bottom_text.upper(), font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) // 2
        bottom_margin_percent = 0.05
        bottom_margin = max(int(height * bottom_margin_percent), 20)
        y = height - text_height - bottom_margin

        outline_width = max(font_size // 20, 3)
        draw_text_with_outline(
            draw, bottom_text.upper(), (x, y), font, outline_width=outline_width
        )

    output = io.BytesIO()

    base_image.save(output, format="PNG")
    output.seek(0)

    return ContentFile(output.getvalue(), name=f"meme.png")
