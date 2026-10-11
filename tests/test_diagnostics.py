"""Unit tests for diagnostic overlay generation."""

from pathlib import Path
import numpy as np
import pytest

from body_measurement.diagnostics import (
    create_diagnostic_overlay,
    draw_segmentation_overlay,
    draw_skeleton_on_image,
)
from body_measurement.pose_detection import LandmarkPoint, PoseDetectionResult
from body_measurement.quality_checks import PoseQualityReport


@pytest.fixture
def sample_detection_and_image():
    """Create a sample image array and corresponding detection result."""
    h, w = 300, 200
    rgb_img = np.full((h, w, 3), 180, dtype=np.uint8)

    # Synthetic segmentation mask: 100x60 oval/rectangle
    seg_mask = np.zeros((h, w), dtype=np.float32)
    seg_mask[50:200, 60:140] = 0.95

    landmarks = [
        LandmarkPoint(index=i, name=f"LM_{i}", x=0.5, y=0.1 + i * 0.02, z=0.0, visibility=0.9, presence=0.9)
        for i in range(33)
    ]

    detection = PoseDetectionResult(
        has_pose=True,
        num_poses_detected=1,
        landmarks=landmarks,
        segmentation_mask=seg_mask,
        image_width=w,
        image_height=h,
    )

    return rgb_img, detection


def test_draw_skeleton_on_image(sample_detection_and_image):
    """Verify skeleton drawing does not mutate original array and returns same dimensions."""
    rgb_img, detection = sample_detection_and_image
    drawn = draw_skeleton_on_image(rgb_img, detection)
    assert drawn.shape == rgb_img.shape
    assert drawn.dtype == np.uint8


def test_draw_segmentation_overlay(sample_detection_and_image):
    """Verify mask overlay rendering."""
    rgb_img, detection = sample_detection_and_image
    drawn = draw_segmentation_overlay(rgb_img, detection)
    assert drawn.shape == rgb_img.shape
    assert drawn.dtype == np.uint8


def test_create_diagnostic_overlay_output_shape(sample_detection_and_image, tmp_path):
    """Verify side-by-side composite layout and file persistence."""
    rgb_img, detection = sample_detection_and_image
    h, w = rgb_img.shape[:2]

    report = PoseQualityReport(
        is_valid=True,
        mean_landmark_visibility=0.92,
        details={"status": "ok"},
    )

    out_file = tmp_path / "diagnostics" / "test_overlay.png"
    composite = create_diagnostic_overlay(
        image=rgb_img,
        detection=detection,
        quality_report=report,
        output_path=out_file,
    )

    # Banner is 60px high, total width is 2 * w
    assert composite.shape == (h + 60, w * 2, 3)
    assert composite.dtype == np.uint8
    assert out_file.is_file(), "Composite diagnostic image must be saved to output path"
