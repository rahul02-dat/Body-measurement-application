"""Unit tests for scale calibration, body bounds detection, and consistency checks."""

import math
import numpy as np
import pytest

from body_measurement.pose_detection import LandmarkPoint, PoseDetectionResult, PoseLandmarkIndex
from body_measurement.scale_calibration import (
    BodyBounds,
    ScaleCalibrationResult,
    calibrate_scale,
    calculate_torso_tilt_degrees,
    detect_vertical_body_bounds,
    simulate_perspective_scale_sensitivity,
    verify_pair_scale_consistency,
)


@pytest.fixture
def mock_detection():
    """Create a standardized mock pose detection in 1000x500 image."""
    h, w = 1000, 500
    landmarks = []
    for i in range(33):
        # Head at y = 0.15 (150px)
        # Shoulders at y = 0.25 (250px)
        # Hips at y = 0.50 (500px)
        # Feet at y = 0.90 (900px)
        if i in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            y = 0.15
        elif i in [11, 12]:
            y = 0.25
        elif i in [23, 24]:
            y = 0.50
        elif i in [27, 28, 29, 30, 31, 32]:
            y = 0.90
        else:
            y = 0.40

        landmarks.append(
            LandmarkPoint(
                index=i,
                name=f"LM_{i}",
                x=0.5,
                y=y,
                z=0.0,
                visibility=0.95,
                presence=0.95,
            )
        )

    return PoseDetectionResult(
        has_pose=True,
        num_poses_detected=1,
        landmarks=landmarks,
        image_width=w,
        image_height=h,
    )


def test_valid_scale_calibration(mock_detection):
    """Verify standard scale calibration calculates positive pixels_per_cm and includes assumptions."""
    result = calibrate_scale(height_cm=175.0, detection=mock_detection)
    assert result.is_valid is True
    assert result.pixels_per_cm > 0.0
    assert result.cm_per_pixel > 0.0
    assert pytest.approx(result.pixels_per_cm * result.cm_per_pixel, 0.001) == 1.0
    assert result.body_span_pixels > 0
    assert len(result.assumptions) >= 4
    assert result.torso_tilt_degrees < 2.0


@pytest.mark.parametrize("invalid_height", [
    float("nan"),
    float("inf"),
    -175.0,
    0.0,
])
def test_reject_non_finite_or_zero_height(mock_detection, invalid_height):
    """Verify non-finite or negative heights produce structured rejection."""
    result = calibrate_scale(height_cm=invalid_height, detection=mock_detection)
    assert result.is_valid is False
    assert "INVALID_NON_FINITE_HEIGHT" in result.rejection_reasons


@pytest.mark.parametrize("out_of_bounds_height", [50.0, 95.0, 240.0])
def test_reject_out_of_bounds_height(mock_detection, out_of_bounds_height):
    """Verify anthropometrically invalid heights are rejected."""
    result = calibrate_scale(height_cm=out_of_bounds_height, detection=mock_detection)
    assert result.is_valid is False
    assert "HEIGHT_OUT_OF_ANTHROPOMETRIC_BOUNDS" in result.rejection_reasons


def test_detect_vertical_body_bounds_hybrid(mock_detection):
    """Verify segmentation mask refines crown and sole bounds."""
    h, w = 1000, 500
    # Synthetic mask: top at y=110 (crown above eyes), bottom at y=920 (soles below ankles)
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[110:921, 200:300] = 255

    bounds = detect_vertical_body_bounds(mock_detection, binary_mask=mask)
    assert bounds.top_y_px == 110
    assert bounds.bottom_y_px == 920
    assert bounds.span_px == (920 - 110 + 1)
    assert bounds.is_reliable is True
    assert "hybrid" in bounds.source


def test_reject_cropped_head(mock_detection):
    """Verify head touching top frame edge marks bounds unreliable."""
    # Place nose at y=0.005 (5px in 1000px height)
    landmarks = list(mock_detection.landmarks)
    landmarks[PoseLandmarkIndex.NOSE] = LandmarkPoint(
        index=0, name="NOSE", x=0.5, y=0.005, z=0.0, visibility=0.9
    )
    mock_detection.landmarks = landmarks

    result = calibrate_scale(height_cm=175.0, detection=mock_detection)
    assert result.is_valid is False
    assert any("top frame border" in r for r in result.rejection_reasons)


def test_reject_cropped_feet(mock_detection):
    """Verify feet touching bottom frame edge marks bounds unreliable."""
    # Place foot at y=0.995 (995px in 1000px height)
    landmarks = list(mock_detection.landmarks)
    landmarks[PoseLandmarkIndex.LEFT_FOOT_INDEX] = LandmarkPoint(
        index=31, name="LEFT_FOOT_INDEX", x=0.5, y=0.995, z=0.0, visibility=0.9
    )
    mock_detection.landmarks = landmarks

    result = calibrate_scale(height_cm=175.0, detection=mock_detection)
    assert result.is_valid is False
    assert any("bottom frame border" in r for r in result.rejection_reasons)


def test_reject_torso_tilt_slouching(mock_detection):
    """Verify significant torso tilt (> 8 degrees) is rejected."""
    landmarks = list(mock_detection.landmarks)
    # Tilt shoulders significantly to the right: x = 0.70 while hips at x = 0.50
    # dy = 0.25 (250px), dx = 0.20 (100px normalized) -> atan2(0.2, 0.25) ~ 38 degrees
    landmarks[PoseLandmarkIndex.LEFT_SHOULDER] = LandmarkPoint(
        index=11, name="LS", x=0.68, y=0.25, z=0.0, visibility=0.9
    )
    landmarks[PoseLandmarkIndex.RIGHT_SHOULDER] = LandmarkPoint(
        index=12, name="RS", x=0.72, y=0.25, z=0.0, visibility=0.9
    )
    mock_detection.landmarks = landmarks

    tilt = calculate_torso_tilt_degrees(mock_detection)
    assert tilt > 8.0

    result = calibrate_scale(height_cm=175.0, detection=mock_detection, max_tilt_degrees=8.0)
    assert result.is_valid is False
    assert any("POSTURE_TILT_OR_SLOUCHING_DETECTED" in r for r in result.rejection_reasons)


def test_pair_scale_consistency_matching(mock_detection):
    """Verify matching front and side scales within 5% tolerance pass."""
    front_scale = calibrate_scale(height_cm=175.0, detection=mock_detection)
    side_scale = calibrate_scale(height_cm=175.0, detection=mock_detection)

    pair_res = verify_pair_scale_consistency(front_scale, side_scale, max_discrepancy_fraction=0.05)
    assert pair_res.is_valid is True
    assert pair_res.scale_discrepancy_fraction == 0.0
    assert pair_res.effective_pixels_per_cm == front_scale.pixels_per_cm


def test_pair_scale_consistency_rejected_on_discrepancy(mock_detection):
    """Verify mismatched scale (> 5% discrepancy) is rejected."""
    front_scale = calibrate_scale(height_cm=175.0, detection=mock_detection)

    # Simulate side photo taken from farther away (shorter span in pixels)
    h, w = 1000, 500
    side_landmarks = [
        LandmarkPoint(lm.index, lm.name, lm.x, lm.y * 0.85, lm.z, lm.visibility)
        for lm in mock_detection.landmarks
    ]
    side_detection = PoseDetectionResult(
        has_pose=True,
        num_poses_detected=1,
        landmarks=side_landmarks,
        image_width=w,
        image_height=h,
    )
    side_scale = calibrate_scale(height_cm=175.0, detection=side_detection)

    pair_res = verify_pair_scale_consistency(front_scale, side_scale, max_discrepancy_fraction=0.05)
    assert pair_res.is_valid is False
    assert any("INCONSISTENT_CAPTURE_DISTANCE_BETWEEN_VIEWS" in r for r in pair_res.rejection_reasons)


def test_simulate_perspective_scale_sensitivity():
    """Verify sensitivity experiment function outputs variations across tilt range."""
    sim = simulate_perspective_scale_sensitivity(
        nominal_height_cm=175.0,
        distance_m=2.8,
        focal_length_px=1200.0,
        tilt_degrees_range=(-5.0, 0.0, 5.0),
    )
    assert "tilt_+0.0deg_px_per_cm" in sim
    assert "tilt_+5.0deg_px_per_cm" in sim
    assert "tilt_-5.0deg_px_per_cm" in sim
    # Small pitch tilt slightly reduces projected vertical height by cos(tilt)
    assert sim["tilt_+5.0deg_px_per_cm"] < sim["tilt_+0.0deg_px_per_cm"]
