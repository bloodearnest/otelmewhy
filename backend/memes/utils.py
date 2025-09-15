import io
import os
import re
import httpx
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.conf import settings


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


def load_emoji_font(size):
    """Load emoji font for rendering emoji characters."""
    try:
        # Try different emoji-capable fonts
        emoji_fonts = [
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for font_path in emoji_fonts:
            try:
                return ImageFont.truetype(font_path, size)
            except (OSError, IOError):
                continue
        return None
    except:
        return None


def is_emoji(char):
    """Check if a character is an emoji using Unicode ranges."""
    # Basic emoji ranges (not exhaustive but covers most common emojis)
    emoji_ranges = [
        (0x1F600, 0x1F64F),  # Emoticons
        (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
        (0x1F680, 0x1F6FF),  # Transport and Map
        (0x1F1E0, 0x1F1FF),  # Regional indicators (flags)
        (0x2600, 0x26FF),  # Misc symbols
        (0x2700, 0x27BF),  # Dingbats
        (0xFE00, 0xFE0F),  # Variation selectors
        (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
        (0x1F018, 0x1F270),  # Various symbols
    ]

    char_code = ord(char)
    return any(start <= char_code <= end for start, end in emoji_ranges)


def fetch_image(image_url):
    """Fetch image from URL and return PIL Image object."""
    response = httpx.get(image_url, follow_redirects=True)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))


def generate_meme(image_url, top_text="", bottom_text=""):
    """Generate a meme by adding text to an image."""
    # Fetch the base image
    base_image = fetch_image(image_url)

    # Convert to RGB if needed (handle transparency)
    if base_image.mode in ("RGBA", "LA"):
        # Create white background for transparent images
        background = Image.new("RGB", base_image.size, (255, 255, 255))
        background.paste(
            base_image,
            mask=base_image.split()[-1] if base_image.mode == "RGBA" else None,
        )
        base_image = background
    elif base_image.mode != "RGB":
        base_image = base_image.convert("RGB")

    # Create a drawing context
    draw = ImageDraw.Draw(base_image)

    # Image dimensions
    width, height = base_image.size

    # Calculate optimal font size based on text length and image dimensions
    def calculate_font_size(text, image_width, image_height):
        if not text:
            return 40  # Default size for empty text

        # Start with base size based on image dimensions (quadrupled)
        max_font_size = min(image_width // 2, image_height // 3)

        # Create a test font to measure text
        test_font = load_impact_font(max_font_size)
        if test_font == ImageFont.load_default():
            max_font_size = 40  # Fallback for default font

        # Iteratively reduce font size until text fits with some margin
        margin_percent = 0.1  # 10% margin on each side
        margin = image_width * margin_percent
        available_width = image_width - (2 * margin)

        font_size = max_font_size
        while font_size > 20:  # Minimum readable size
            try:
                current_font = load_impact_font(font_size)

                # Calculate text width with mixed fonts (regular + emoji)
                text_width = 0
                emoji_font = load_emoji_font(font_size)

                for char in text.upper():
                    if is_emoji(char) and emoji_font is not None:
                        bbox = emoji_font.getbbox(char)
                    else:
                        bbox = current_font.getbbox(char)
                    text_width += bbox[2] - bbox[0]

                if text_width <= available_width:
                    return font_size

                font_size = int(font_size * 0.9)  # Reduce by 10%
            except Exception as e:
                break

        return max(font_size, 20)  # Ensure minimum size

    # Calculate font sizes for top and bottom text
    top_font_size = calculate_font_size(top_text, width, height)
    bottom_font_size = calculate_font_size(bottom_text, width, height)

    # Use the smaller of the two to maintain consistency
    font_size = (
        min(top_font_size, bottom_font_size)
        if top_text and bottom_text
        else max(top_font_size, bottom_font_size, 40)
    )

    # Load font with calculated size
    font = load_impact_font(font_size)

    # Function to draw text with outline and emoji support
    def draw_text_with_outline(
        draw,
        text,
        position,
        font,
        fill_color="white",
        outline_color="black",
        outline_width=2,
    ):
        x, y = position
        # Ensure text is uppercase (but preserve emojis)
        text = text.upper()

        # Load emoji font
        emoji_font = load_emoji_font(font.size if hasattr(font, "size") else font_size)

        # If no emoji font available, fall back to regular rendering
        if emoji_font is None:
            # Draw outline
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
            # Draw main text
            draw.text(position, text, font=font, fill=fill_color)
            return

        # Render character by character with font switching
        current_x = x
        for char in text:
            if is_emoji(char):
                # Use emoji font (no outline for emojis as they're colorful)
                draw.text((current_x, y), char, font=emoji_font, fill=fill_color)
                char_width = emoji_font.getbbox(char)[2] - emoji_font.getbbox(char)[0]
            else:
                # Use regular font with outline
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text(
                                (current_x + dx, y + dy),
                                char,
                                font=font,
                                fill=outline_color,
                            )
                draw.text((current_x, y), char, font=font, fill=fill_color)
                char_width = font.getbbox(char)[2] - font.getbbox(char)[0]

            current_x += char_width

    # Draw top text
    if top_text:
        # Get text bounding box
        bbox = draw.textbbox((0, 0), top_text.upper(), font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center horizontally, position at top with margin
        x = (width - text_width) // 2
        top_margin_percent = 0.05  # 5% of image height
        top_margin = max(int(height * top_margin_percent), 20)  # minimum 20px
        y = top_margin

        # Calculate outline width based on font size
        outline_width = max(font_size // 20, 3)  # 5% of font size, minimum 3px
        draw_text_with_outline(
            draw, top_text.upper(), (x, y), font, outline_width=outline_width
        )

    # Draw bottom text
    if bottom_text:
        # Get text bounding box
        bbox = draw.textbbox((0, 0), bottom_text.upper(), font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center horizontally, position at bottom with margin
        x = (width - text_width) // 2
        bottom_margin_percent = 0.05  # 5% of image height
        bottom_margin = max(int(height * bottom_margin_percent), 20)  # minimum 20px
        y = height - text_height - bottom_margin

        # Calculate outline width based on font size
        outline_width = max(font_size // 20, 3)  # 5% of font size, minimum 3px
        draw_text_with_outline(
            draw, bottom_text.upper(), (x, y), font, outline_width=outline_width
        )

    # Save to BytesIO
    output = io.BytesIO()
    base_image.save(output, format="PNG")
    output.seek(0)

    return ContentFile(output.getvalue(), name=f"meme.png")
