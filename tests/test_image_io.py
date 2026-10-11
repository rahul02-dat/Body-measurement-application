"""Unit tests for image loading, validation, and format normalization."""

from pathlib import Path
import numpy as np
from PIL import Image
import pytest

from body_measurement.image_io import (
    ImageLoadError,
    LoadedImage,
    load_and_validate_image,
    load_participant_images,
)
from body_measurement.schemas import ParticipantRecord


@pytest.fixture
def synthetic_images_dir(tmp_path):
    """Generates synthetic test images in multiple formats and color modes."""
    # Standard RGB JPEG
    rgb_img = Image.new("RGB", (320, 480), color=(128, 64, 200))
    rgb_path = tmp_path / "test_rgb.jpg"
    rgb_img.save(rgb_path, "JPEG")

    # RGBA PNG
    rgba_img = Image.new("RGBA", (200, 300), color=(100, 150, 200, 128))
    rgba_path = tmp_path / "test_rgba.png"
    rgba_img.save(rgba_path, "PNG")

    # Grayscale WebP
    gray_img = Image.new("L", (150, 150), color=100)
    gray_path = tmp_path / "test_gray.webp"
    gray_img.save(gray_path, "WEBP")

    return {
        "rgb": rgb_path,
        "rgba": rgba_path,
        "gray": gray_path,
        "dir": tmp_path,
    }


def test_load_valid_rgb_image(synthetic_images_dir):
    """Verify loading standard RGB JPEG produces valid LoadedImage."""
    img = load_and_validate_image(synthetic_images_dir["rgb"])
    assert isinstance(img, LoadedImage)
    assert img.width == 320
    assert img.height == 480
    assert img.channels == 3
    assert img.rgb_array.shape == (480, 320, 3)
    assert img.rgb_array.dtype == np.uint8


def test_convert_rgba_to_rgb(synthetic_images_dir):
    """Verify RGBA image is safely converted to 3-channel RGB."""
    img = load_and_validate_image(synthetic_images_dir["rgba"])
    assert img.channels == 3
    assert img.rgb_array.shape == (300, 200, 3)
    assert img.rgb_array.dtype == np.uint8


def test_convert_grayscale_to_rgb(synthetic_images_dir):
    """Verify grayscale image is converted to 3-channel RGB."""
    img = load_and_validate_image(synthetic_images_dir["gray"])
    assert img.channels == 3
    assert img.rgb_array.shape == (150, 150, 3)
    assert img.rgb_array.dtype == np.uint8


def test_load_nonexistent_image():
    """Verify loading nonexistent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_and_validate_image(Path("missing_file_123.jpg"))


def test_reject_unsupported_extension(tmp_path):
    """Verify unsupported extensions (e.g. .bmp, .gif, .txt) are rejected."""
    unsupported = tmp_path / "image.bmp"
    unsupported.write_text("dummy")
    with pytest.raises(ImageLoadError) as excinfo:
        load_and_validate_image(unsupported)
    assert "Unsupported image extension" in str(excinfo.value)


def test_reject_corrupt_image(tmp_path):
    """Verify corrupted image bytes raise ImageLoadError."""
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00BAD_BYTES_TRUNCATED")
    with pytest.raises(ImageLoadError) as excinfo:
        load_and_validate_image(corrupt_file)
    assert "Cannot identify or decode image file" in str(excinfo.value) or "Error loading image" in str(excinfo.value)


def test_permissive_small_resolution(tmp_path):
    """Verify permissive policy allows non-zero small image resolutions."""
    tiny_img = Image.new("RGB", (20, 20), color=(255, 0, 0))
    tiny_path = tmp_path / "tiny.png"
    tiny_img.save(tiny_path, "PNG")

    loaded = load_and_validate_image(tiny_path)
    assert loaded.width == 20
    assert loaded.height == 20


def test_load_participant_images_pair(synthetic_images_dir):
    """Verify loading both front and side images for a ParticipantRecord."""
    record = ParticipantRecord(
        participant_id="SYNTH_PAIR_01",
        front_image_path="test_rgb.jpg",
        side_image_path="test_rgba.png",
        height_cm=170.0,
        chest_tape_cm=92.0,
        waist_tape_cm=78.0,
        hip_tape_cm=96.0,
        lighting_adequate=True,
        posture_upright=True,
        feet_visible=True,
        clothing_tight=True,
        protocol_version="v1.0",
        consent_given=True,
        retention_agreed=True,
    )

    front_img, side_img = load_participant_images(record, base_dir=synthetic_images_dir["dir"])
    assert front_img.width == 320
    assert front_img.height == 480
    assert side_img.width == 200
    assert side_img.height == 300
