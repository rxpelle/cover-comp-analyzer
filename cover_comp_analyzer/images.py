"""Image processing for cover analysis.

Handles loading, thumbnail generation, dominant color extraction,
and base64 encoding for the Claude Vision API.
"""

import base64
import io
import logging
from collections import Counter
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}


def load_image(path):
    """Load an image from disk, return as RGB PIL Image."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported image format: {path.suffix}")
    return Image.open(path).convert('RGB')


def make_thumbnail(img, width):
    """Resize image to a given width, maintaining aspect ratio."""
    ratio = width / img.width
    height = int(img.height * ratio)
    return img.resize((width, height), Image.LANCZOS)


def image_to_base64(img, format='PNG'):
    """Convert PIL Image to base64 string for API calls."""
    buf = io.BytesIO()
    img.save(buf, format=format)
    return base64.standard_b64encode(buf.getvalue()).decode('utf-8')


def get_media_type(format='PNG'):
    """Return the MIME type for an image format."""
    types = {
        'PNG': 'image/png',
        'JPEG': 'image/jpeg',
        'JPG': 'image/jpeg',
        'WEBP': 'image/webp',
    }
    return types.get(format.upper(), 'image/png')


def extract_dominant_colors(img, num_colors=5):
    """Extract dominant colors from an image using quantization.

    Returns a list of dicts: [{'rgb': (r, g, b), 'hex': '#RRGGBB', 'percentage': float}]
    """
    # Resize for speed
    small = img.copy()
    small.thumbnail((150, 150))

    # Quantize to reduce colors
    quantized = small.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()
    pixels = list(quantized.getdata())
    total = len(pixels)

    # Count pixel frequency per palette index
    counts = Counter(pixels)

    colors = []
    for idx, count in counts.most_common(num_colors):
        r, g, b = palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2]
        colors.append({
            'rgb': (r, g, b),
            'hex': f'#{r:02x}{g:02x}{b:02x}',
            'percentage': round(count / total * 100, 1),
        })

    return colors


def get_image_stats(img):
    """Get basic image statistics: dimensions, aspect ratio, file size estimate."""
    width, height = img.size
    return {
        'width': width,
        'height': height,
        'aspect_ratio': round(width / height, 3),
        'megapixels': round(width * height / 1_000_000, 2),
    }


def load_comp_folder(folder_path, max_images=20):
    """Load all supported images from a folder.

    Returns list of (filename, PIL Image) tuples, sorted by filename.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    images = []
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() in SUPPORTED_EXTENSIONS and not f.name.startswith('.'):
            try:
                img = load_image(f)
                images.append((f.name, img))
                if len(images) >= max_images:
                    break
            except Exception as e:
                logger.warning(f"Skipping {f.name}: {e}")

    return images
