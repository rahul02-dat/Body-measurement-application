"""Unit tests for segmentation mask processing and geometric extraction."""

import numpy as np
import pytest

from body_measurement.segmentation import (
    calculate_mask_coverage,
    extract_binary_mask,
    extract_bounding_box,
    extract_mask_width_at_y,
    keep_largest_component,
)


def test_extract_binary_mask():
    """Verify thresholding converts float probabilities to binary uint8."""
    prob_mask = np.array([
        [0.1, 0.49, 0.5, 0.9],
        [0.0, 0.2, 0.8, 1.0],
    ], dtype=np.float32)

    binary = extract_binary_mask(prob_mask, threshold=0.5)
    assert binary.dtype == np.uint8
    assert binary[0, 0] == 0
    assert binary[0, 1] == 0
    assert binary[0, 2] == 255
    assert binary[0, 3] == 255
    assert binary[1, 2] == 255


def test_extract_bounding_box():
    """Verify tight bounding box coordinates on known shape."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    # Place a 30x40 rectangle at y: 20..49, x: 10..49
    mask[20:50, 10:50] = 255

    bbox = extract_bounding_box(mask)
    assert bbox is not None
    ymin, xmin, ymax, xmax = bbox
    assert ymin == 20
    assert ymax == 49
    assert xmin == 10
    assert xmax == 49


def test_extract_bounding_box_empty():
    """Verify empty mask returns None."""
    mask = np.zeros((50, 50), dtype=np.uint8)
    assert extract_bounding_box(mask) is None


def test_extract_mask_width_at_y():
    """Verify horizontal width span at specified y row."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    # At row 30, set pixels from x=20 to x=59 (width = 40)
    mask[30, 20:60] = 255

    width = extract_mask_width_at_y(mask, y=30)
    assert width == 40

    # Row with no pixels
    assert extract_mask_width_at_y(mask, y=0) == 0
    # Out of bounds row
    assert extract_mask_width_at_y(mask, y=200) == 0


def test_calculate_mask_coverage():
    """Verify foreground coverage ratio calculation."""
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[:5, :] = 255  # 50 pixels out of 100
    assert pytest.approx(calculate_mask_coverage(mask), 0.01) == 0.5


def test_keep_largest_component():
    """Verify connected component filtering keeps primary blob and removes noise."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    # Small noise blob (area 4)
    mask[5:7, 5:7] = 255
    # Large main blob (area 400)
    mask[20:40, 20:40] = 255

    cleaned = keep_largest_component(mask)
    # Noise should be removed
    assert np.count_nonzero(cleaned[5:7, 5:7]) == 0
    # Main blob should remain
    assert np.count_nonzero(cleaned[20:40, 20:40]) == 400
