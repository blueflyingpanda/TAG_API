import io
import logging
import uuid
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from conf import settings

logger = logging.getLogger('images')

COVER_WIDTH = 640
COVER_HEIGHT = 360  # 16:9, matches the theme thumbnail
COVER_MAX_BYTES = 256 * 1024
UPLOAD_MAX_BYTES = 5 * 1024 * 1024
MAX_SOURCE_PIXELS = 40_000_000
COVERS_SUBDIR = 'covers'

Image.MAX_IMAGE_PIXELS = MAX_SOURCE_PIXELS


class InvalidImageError(ValueError):
    """Upload is not a usable image"""


def make_cover(data: bytes) -> bytes:
    """Center-crop to 16:9, resize to COVER_WIDTH x COVER_HEIGHT and encode as WebP under COVER_MAX_BYTES"""
    try:
        with Image.open(io.BytesIO(data)) as src:
            image = ImageOps.exif_transpose(src)
            image = image.convert('RGBA' if image.has_transparency_data else 'RGB')
            image = ImageOps.fit(image, (COVER_WIDTH, COVER_HEIGHT), Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise InvalidImageError('Unsupported or corrupted image') from e

    for quality in (85, 75, 65, 50, 35, 20):
        buffer = io.BytesIO()
        image.save(buffer, format='WEBP', quality=quality, method=6)
        if buffer.tell() <= COVER_MAX_BYTES:
            return buffer.getvalue()
    raise InvalidImageError('Image cannot be compressed below the size limit')


def save_cover(content: bytes) -> str:
    """Write encoded cover to media dir, return its filename relative to media_dir"""
    filename = f'{COVERS_SUBDIR}/{uuid.uuid4().hex}.webp'
    path = Path(settings.media_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return filename


def delete_cover_file(filename: str) -> None:
    try:
        (Path(settings.media_dir) / filename).unlink(missing_ok=True)
    except OSError:
        logger.exception('Could not delete cover file %s', filename)
