"""Unit and integration tests for Ramanujan ellipse baseline and torso cross-section geometry."""

import math
import numpy as np
import pytest

from body_measurement.diagnostics import draw_cross_section_overlay
from body_measurement.measurement_geometry import (
    calculate_ellipse_circumference,
    compute_body_measurements,
    compute_cross_section,
    compute_exploratory_measurements,
    locate_cross_section_levels,
)
from body_measurement.pose_detection import LandmarkPoint, PoseDetectionResult, PoseLandmarkIndex
from body_measurement.scale_calibration import BodyBounds, ScaleCalibrationResult


def test_ramanujan_circle_exact():
    """Verify circle special case (width == depth) matches 2*pi*r exactly."""
    # Diameter = 20.0 cm -> radius = 10.0 cm -> circumference = 2 * pi * 10 = 62.83 cm
    circ = calculate_ellipse_circumference(20.0, 20.0)
    expected = round(2.0 * math.pi * 10.0, 2)
    assert circ == expected


def test_ramanujan_known_ellipse():
    """Verify Ramanujan formula against known analytical ellipse values."""
    # Semi-axes: a = 5.0 cm (width = 10.0), b = 3.0 cm (depth = 6.0)
    # C ≈ pi * (3*(5+3) - sqrt((15+3)*(5+9))) = pi * (24 - sqrt(252)) ≈ 25.53
    circ = calculate_ellipse_circumference(width_cm=10.0, depth_cm=6.0)
    assert circ == 25.53


@pytest.mark.parametrize("invalid_w, invalid_d", [
    (0.0, 10.0),
    (10.0, 0.0),
    (-5.0, 10.0),
    (10.0, -5.0),
    (float("nan"), 10.0),
    (10.0, float("inf")),
])
def test_ramanujan_invalid_inputs(invalid_w, invalid_d):
    """Verify non-positive or non-finite inputs raise ValueError."""
    with pytest.raises(ValueError):
        calculate_ellipse_circumference(invalid_w, invalid_d)


@pytest.fixture
def synthetic_torso_pair():
    """Build synthetic front and side detections, masks, and scale objects."""
    h, w = 1000, 500

    # Build landmark sets
    def make_detection():
        lms = []
        for i in range(33):
            if i in [11, 12]:  # Shoulders at y = 0.20 (200px)
                y = 0.20
            elif i in [23, 24]:  # Hips at y = 0.60 (600px)
                y = 0.60
            elif i in [27, 28]:  # Ankles at y = 0.90 (900px)
                y = 0.90
            else:
                y = 0.40

            x = 0.35 if i == 11 else (0.65 if i == 12 else 0.5)
            lms.append(
                LandmarkPoint(index=i, name=f"LM_{i}", x=x, y=y, z=0.0, visibility=0.95, presence=0.95)
            )

        return PoseDetectionResult(
            has_pose=True,
            num_poses_detected=1,
            landmarks=lms,
            image_width=w,
            image_height=h,
        )

    front_det = make_detection()
    side_det = make_detection()

    # Front mask with hourglass waist:
    # Chest (row 340): width = 140px
    # Waist (row 450): width = 100px (narrowest)
    # Hip (row 620): width = 160px (widest)
    front_mask = np.zeros((h, w), dtype=np.uint8)
    front_mask[200:350, 180:320] = 255  # Upper chest width 140
    front_mask[350:500, 200:300] = 255  # Waist width 100
    front_mask[500:700, 170:330] = 255  # Hip width 160
    front_mask[700:920, 220:280] = 255  # Legs

    # Side mask with profile depth:
    side_mask = np.zeros((h, w), dtype=np.uint8)
    side_mask[200:350, 200:300] = 255  # Chest depth 100
    side_mask[350:500, 210:290] = 255  # Waist depth 80
    side_mask[500:700, 190:310] = 255  # Hip depth 120
    side_mask[700:920, 220:280] = 255  # Legs

    # Scale: 5.0 pixels per cm -> cm_per_pixel = 0.20
    dummy_bounds = BodyBounds(100, 920, 821, h, "test", True)
    scale = ScaleCalibrationResult(
        pixels_per_cm=5.0,
        cm_per_pixel=0.20,
        entered_height_cm=175.0,
        body_span_pixels=821,
        bounds=dummy_bounds,
        torso_tilt_degrees=0.0,
        is_valid=True,
    )

    return {
        "front_det": front_det,
        "side_det": side_det,
        "front_mask": front_mask,
        "side_mask": side_mask,
        "scale": scale,
    }


def test_locate_cross_section_levels_order(synthetic_torso_pair):
    """Verify cross-section levels are found in correct anatomical top-to-bottom order."""
    levels = locate_cross_section_levels(
        front_detection=synthetic_torso_pair["front_det"],
        front_mask=synthetic_torso_pair["front_mask"],
        side_detection=synthetic_torso_pair["side_det"],
        side_mask=synthetic_torso_pair["side_mask"],
    )

    f_chest, s_chest = levels["chest"]
    f_waist, s_waist = levels["waist"]
    f_hip, s_hip = levels["hip"]

    assert f_chest < f_waist < f_hip
    assert s_chest < s_waist < s_hip


def test_compute_cross_section_measurement(synthetic_torso_pair):
    """Verify single cross section extraction and calculation."""
    cs = compute_cross_section(
        name="waist",
        front_y_px=450,
        side_y_px=450,
        front_mask=synthetic_torso_pair["front_mask"],
        side_mask=synthetic_torso_pair["side_mask"],
        front_scale=synthetic_torso_pair["scale"],
        side_scale=synthetic_torso_pair["scale"],
    )

    assert cs.is_valid is True
    # width_px = 100 -> width_cm = 100 * 0.20 = 20.0 cm
    assert cs.width_cm == 20.0
    # depth_px = 80 -> depth_cm = 80 * 0.20 = 16.0 cm
    assert cs.depth_cm == 16.0
    # Ramanujan circumference for 20.0 x 16.0
    expected_circ = calculate_ellipse_circumference(20.0, 16.0)
    assert cs.circumference_cm == expected_circ


def test_compute_cross_section_zero_width_fails(synthetic_torso_pair):
    """Verify attempting to measure empty pixel row returns structured failure."""
    cs = compute_cross_section(
        name="empty_row",
        front_y_px=10,  # Row 10 is outside silhouette (zero pixels)
        side_y_px=10,
        front_mask=synthetic_torso_pair["front_mask"],
        side_mask=synthetic_torso_pair["side_mask"],
        front_scale=synthetic_torso_pair["scale"],
        side_scale=synthetic_torso_pair["scale"],
    )

    assert cs.is_valid is False
    assert "Zero pixel width" in cs.rejection_reason


def test_compute_exploratory_measurements(synthetic_torso_pair):
    """Verify shoulder width and inseam calculations."""
    sh_m, inseam_m = compute_exploratory_measurements(
        front_detection=synthetic_torso_pair["front_det"],
        front_scale=synthetic_torso_pair["scale"],
    )

    assert sh_m is not None
    assert sh_m.name == "shoulder_width"
    assert sh_m.is_valid is True
    assert sh_m.is_exploratory is True
    assert sh_m.value_cm > 0

    assert inseam_m is not None
    assert inseam_m.name == "inseam"
    assert inseam_m.is_valid is True
    assert inseam_m.is_exploratory is True
    assert inseam_m.value_cm > 0


def test_compute_body_measurements_end_to_end(synthetic_torso_pair):
    """Verify complete geometric pipeline across a paired set."""
    result = compute_body_measurements(
        front_detection=synthetic_torso_pair["front_det"],
        front_mask=synthetic_torso_pair["front_mask"],
        front_scale=synthetic_torso_pair["scale"],
        side_detection=synthetic_torso_pair["side_det"],
        side_mask=synthetic_torso_pair["side_mask"],
        side_scale=synthetic_torso_pair["scale"],
        include_exploratory=True,
    )

    assert result.is_valid is True
    assert result.chest.is_valid is True
    assert result.waist.is_valid is True
    assert result.hip.is_valid is True
    assert result.chest.circumference_cm > 0
    assert result.waist.circumference_cm > 0
    assert result.hip.circumference_cm > 0
    assert result.shoulder_width is not None
    assert result.inseam is not None
    assert len(result.limitations) >= 3


def test_draw_cross_section_overlay():
    """Verify overlay drawing returns copy with matching shape and dtype."""
    dummy_img = np.full((500, 300, 3), 100, dtype=np.uint8)
    levels = {"chest": 150, "waist": 250, "hip": 350}
    vals = {"chest": 95.0, "waist": 80.0, "hip": 100.0}

    overlay = draw_cross_section_overlay(dummy_img, levels, vals)
    assert overlay.shape == dummy_img.shape
    assert overlay.dtype == np.uint8
