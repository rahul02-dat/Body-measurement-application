"""Safe image loading, integrity validation, and color-space normalization."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
from PIL import Image, UnidentifiedImageError

from body_measurement.config import DEFAULT_IMAGE_CONFIG
from body_measurement.schemas import ParticipantRecord


class ImageLoadError(Exception):
    """Raised when an image cannot be read, decoded, or validated."""

    def __init__(self, message: str, image_path: Optional[Path] = None):
        super().__init__(message)
        self.image_path = image_path


@dataclass(frozen=True)
class LoadedImage:
    """Validated image in memory with standard RGB uint8 array and dimension metadata."""

    path: Path
    rgb_array: np.ndarray
    width: int
    height: int
    channels: int = 3

    def __post_init__(self):
        if self.rgb_array.ndim != 3 or self.rgb_array.shape[2] != 3:
            raise ValueError(
                f"Expected RGB image array of shape (H, W, 3), got shape {self.rgb_array.shape}"
            )
        if self.rgb_array.dtype != np.uint8:
            raise ValueError(f"Expected array dtype uint8, got {self.rgb_array.dtype}")


def load_and_validate_image(
    image_path: Union[str, Path],
    max_pixels: Optional[int] = None,
) -> LoadedImage:
    """
    Safely load an image from disk, verify integrity, and convert to standard RGB uint8 array.

    Args:
        image_path: Path to the image file.
        max_pixels: Optional safety ceiling for pixel count (prevents decompression bombs).

    Returns:
        LoadedImage dataclass containing verified RGB numpy array and dimensions.

    Raises:
        FileNotFoundError: If the file does not exist.
        ImageLoadError: If the file is not a regular file, has unsupported format,
                        is corrupt, has zero dimensions, or exceeds max pixel limits.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file does not exist: {path}")
    if not path.is_file():
        raise ImageLoadError(f"Target path is not a regular file: {path}", image_path=path)

    # Check file extension
    ext = path.suffix.lower()
    if ext not in DEFAULT_IMAGE_CONFIG.SUPPORTED_EXTENSIONS:
        raise ImageLoadError(
            f"Unsupported image extension '{ext}' for file {path}. "
            f"Supported extensions: {sorted(DEFAULT_IMAGE_CONFIG.SUPPORTED_EXTENSIONS)}",
            image_path=path,
        )

    effective_max_pixels = max_pixels or DEFAULT_IMAGE_CONFIG.MAX_IMAGE_PIXELS

    # Protect against decompression bombs
    prev_max_pixels = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = effective_max_pixels

    try:
        with Image.open(path) as img:
            # Check for corrupt image headers / truncate
            img.load()

            width, height = img.size
            if width <= 0 or height <= 0:
                raise ImageLoadError(
                    f"Invalid image dimensions ({width}x{height}) in {path}. Dimensions must be > 0.",
                    image_path=path,
                )

            # Convert to standard 3-channel RGB (handles RGBA, L, CMYK, Palette)
            if img.mode != "RGB":
                rgb_img = img.convert("RGB")
            else:
                rgb_img = img

            rgb_array = np.array(rgb_img, dtype=np.uint8)

            return LoadedImage(
                path=path,
                rgb_array=rgb_array,
                width=width,
                height=height,
                channels=3,
            )

    except UnidentifiedImageError as e:
        raise ImageLoadError(f"Cannot identify or decode image file '{path}': {e}", image_path=path) from e
    except Image.DecompressionBombError as e:
        raise ImageLoadError(f"Image exceeds safe decompression pixel limit '{path}': {e}", image_path=path) from e
    except Exception as e:
        raise ImageLoadError(f"Error loading image '{path}': {e}", image_path=path) from e
    finally:
        Image.MAX_IMAGE_PIXELS = prev_max_pixels


def load_participant_images(
    record: ParticipantRecord,
    base_dir: Optional[Union[str, Path]] = None,
) -> Tuple[LoadedImage, LoadedImage]:
    """
    Load both front and side images for a validated participant record.

    Args:
        record: Validated ParticipantRecord.
        base_dir: Optional directory to resolve relative image paths against.

    Returns:
        Tuple of (front_image: LoadedImage, side_image: LoadedImage).
    """
    root = Path(base_dir) if base_dir else Path.cwd()
    front_path = root / record.front_image_path
    side_path = root / record.side_image_path

    front_img = load_and_validate_image(front_path)
    side_img = load_and_validate_image(side_path)

    return front_img, side_img
