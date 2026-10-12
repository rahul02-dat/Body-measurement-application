"""Deterministic geometric baseline estimating body circumferences via Ramanujan's ellipse approximation."""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from body_measurement.pose_detection import PoseDetectionResult, PoseLandmarkIndex
from body_measurement.scale_calibration import ScaleCalibrationResult
from body_measurement.segmentation import extract_mask_width_at_y


ELLIPSE_MODEL_LIMITATIONS: List[str] = [
    "Human cross-sections are approximated as true planar ellipses; actual cross-sections deviate from elliptical geometry.",
    "Loose or thick clothing introduces outward radial bias in width and depth measurements.",
    "Segmentation mask boundary errors and perspective projection directly influence width and depth extraction.",
    "Posture shifts between front and side photographs may induce level-matching discrepancies.",
]


@dataclass
class CrossSectionMeasurement:
    """Measurement for a specific anatomical cross-section level (chest, waist, or hip)."""

    name: str
    front_y_px: int
    side_y_px: int
    width_px: int
    depth_px: int
    width_cm: float
    depth_cm: float
    circumference_cm: float
    is_valid: bool
    rejection_reason: Optional[str] = None


@dataclass
class ExploratoryMeasurement:
    """Exploratory anatomical measurement (shoulder width or inseam)."""

    name: str
    value_cm: float
    pixel_span: float
    is_valid: bool
    is_exploratory: bool = True
    rejection_reason: Optional[str] = None
    notes: str = ""


@dataclass
class GeometricMeasurementResult:
    """Consolidated geometric measurement outputs for an image pair."""

    chest: CrossSectionMeasurement
    waist: CrossSectionMeasurement
    hip: CrossSectionMeasurement
    shoulder_width: Optional[ExploratoryMeasurement] = None
    inseam: Optional[ExploratoryMeasurement] = None
    is_valid: bool = True
    rejection_reasons: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=lambda: list(ELLIPSE_MODEL_LIMITATIONS))


def calculate_ellipse_circumference(width_cm: float, depth_cm: float) -> float:
    """
    Approximate the perimeter of an ellipse using Ramanujan's formula.

    Formula:
        a = width_cm / 2
        b = depth_cm / 2
        C ≈ pi * (3*(a + b) - sqrt((3*a + b) * (a + 3*b)))

    Args:
        width_cm: Front-view horizontal cross-section diameter in centimeters.
        depth_cm: Side-view profile cross-section diameter in centimeters.

    Returns:
        Perimeter circumference in centimeters (rounded to 2 decimal places).

    Raises:
        ValueError: If width_cm or depth_cm are non-finite or non-positive.
    """
    if not math.isfinite(width_cm) or not math.isfinite(depth_cm):
        raise ValueError(f"Width ({width_cm}) and depth ({depth_cm}) must be finite numbers.")
    if width_cm <= 0.0 or depth_cm <= 0.0:
        raise ValueError(f"Width ({width_cm}) and depth ({depth_cm}) must be strictly positive.")

    a = width_cm / 2.0
    b = depth_cm / 2.0

    # Exact closed-form circle case
    if math.isclose(a, b, rel_tol=1e-7):
        return round(2.0 * math.pi * a, 2)

    # Ramanujan's first approximation
    term1 = 3.0 * (a + b)
    term2 = math.sqrt((3.0 * a + b) * (a + 3.0 * b))
    c = math.pi * (term1 - term2)

    return round(float(c), 2)


def _get_torso_anchors(
    detection: PoseDetectionResult,
) -> Optional[Tuple[float, float, float]]:
    """Extract mid-shoulder y, mid-hip y, and torso height span in normalized coordinates."""
    left_sh = detection.get_landmark(PoseLandmarkIndex.LEFT_SHOULDER)
    right_sh = detection.get_landmark(PoseLandmarkIndex.RIGHT_SHOULDER)
    left_hip = detection.get_landmark(PoseLandmarkIndex.LEFT_HIP)
    right_hip = detection.get_landmark(PoseLandmarkIndex.RIGHT_HIP)

    if None in (left_sh, right_sh, left_hip, right_hip):
        return None

    y_sh = (left_sh.y + right_sh.y) / 2.0
    y_hip = (left_hip.y + right_hip.y) / 2.0
    torso_span = y_hip - y_sh

    if torso_span <= 0:
        return None

    return y_sh, y_hip, torso_span


def locate_cross_section_levels(
    front_detection: PoseDetectionResult,
    front_mask: np.ndarray,
    side_detection: PoseDetectionResult,
    side_mask: np.ndarray,
) -> Dict[str, Tuple[int, int]]:
    """
    Locate vertical pixel rows (front_y_px, side_y_px) for chest, waist, and hip.

    Uses anatomical search:
    - Chest: 35% down from mid-shoulders to mid-hips.
    - Waist: Anatomical search for minimum mask width in [50%, 80%] torso band.
    - Hip: Anatomical search for maximum mask width in [85%, 125%] torso/pelvis band.

    Returns:
        Dictionary mapping level name to (front_y_px, side_y_px).
    """
    h_front = front_mask.shape[0]
    h_side = side_mask.shape[0]

    front_anchors = _get_torso_anchors(front_detection)
    side_anchors = _get_torso_anchors(side_detection)

    if front_anchors is None or side_anchors is None:
        raise ValueError("Cannot locate measurement levels: missing shoulder or hip landmarks.")

    f_sh_y, f_hip_y, f_torso_span = front_anchors
    s_sh_y, s_hip_y, s_torso_span = side_anchors

    # 1. Chest Level: ~35% down torso span
    f_chest_norm = f_sh_y + 0.35 * f_torso_span
    s_chest_norm = s_sh_y + 0.35 * s_torso_span
    f_chest_y = int(round(f_chest_norm * h_front))
    s_chest_y = int(round(s_chest_norm * h_side))

    # 2. Waist Level: Anatomical search for narrowest mask width in [50%, 80%] torso span
    waist_start_y = int(round((f_sh_y + 0.50 * f_torso_span) * h_front))
    waist_end_y = int(round((f_sh_y + 0.80 * f_torso_span) * h_front))

    best_waist_y = int(round((f_sh_y + 0.65 * f_torso_span) * h_front))
    min_waist_width = float("inf")

    for y in range(max(0, waist_start_y), min(h_front, waist_end_y + 1)):
        w = extract_mask_width_at_y(front_mask, y)
        if 0 < w < min_waist_width:
            min_waist_width = w
            best_waist_y = y

    # Compute relative torso fraction of detected waist and map to side view
    waist_fraction = (best_waist_y / h_front - f_sh_y) / f_torso_span
    s_waist_y = int(round((s_sh_y + waist_fraction * s_torso_span) * h_side))

    # 3. Hip Level: Anatomical search for widest mask width in [85%, 125%] torso/pelvis band
    hip_start_y = int(round((f_sh_y + 0.85 * f_torso_span) * h_front))
    hip_end_y = int(round((f_sh_y + 1.25 * f_torso_span) * h_front))

    best_hip_y = int(round((f_sh_y + 1.00 * f_torso_span) * h_front))
    max_hip_width = 0

    for y in range(max(0, hip_start_y), min(h_front, hip_end_y + 1)):
        w = extract_mask_width_at_y(front_mask, y)
        if w > max_hip_width:
            max_hip_width = w
            best_hip_y = y

    hip_fraction = (best_hip_y / h_front - f_sh_y) / f_torso_span
    s_hip_y = int(round((s_sh_y + hip_fraction * s_torso_span) * h_side))

    return {
        "chest": (f_chest_y, s_chest_y),
        "waist": (best_waist_y, s_waist_y),
        "hip": (best_hip_y, s_hip_y),
    }


def compute_cross_section(
    name: str,
    front_y_px: int,
    side_y_px: int,
    front_mask: np.ndarray,
    side_mask: np.ndarray,
    front_scale: ScaleCalibrationResult,
    side_scale: ScaleCalibrationResult,
) -> CrossSectionMeasurement:
    """
    Extract width from front mask and depth from side mask at specified rows,
    convert to centimeters, and calculate circumference via Ramanujan's formula.
    """
    width_px = extract_mask_width_at_y(front_mask, front_y_px)
    depth_px = extract_mask_width_at_y(side_mask, side_y_px)

    if width_px <= 0 or depth_px <= 0:
        return CrossSectionMeasurement(
            name=name,
            front_y_px=front_y_px,
            side_y_px=side_y_px,
            width_px=width_px,
            depth_px=depth_px,
            width_cm=0.0,
            depth_cm=0.0,
            circumference_cm=0.0,
            is_valid=False,
            rejection_reason=f"Zero pixel width ({width_px}px) or depth ({depth_px}px) at {name} level.",
        )

    width_cm = round(width_px * front_scale.cm_per_pixel, 2)
    depth_cm = round(depth_px * side_scale.cm_per_pixel, 2)

    try:
        circumference_cm = calculate_ellipse_circumference(width_cm, depth_cm)
        is_valid = True
        rejection_reason = None
    except ValueError as e:
        circumference_cm = 0.0
        is_valid = False
        rejection_reason = str(e)

    return CrossSectionMeasurement(
        name=name,
        front_y_px=front_y_px,
        side_y_px=side_y_px,
        width_px=width_px,
        depth_px=depth_px,
        width_cm=width_cm,
        depth_cm=depth_cm,
        circumference_cm=circumference_cm,
        is_valid=is_valid,
        rejection_reason=rejection_reason,
    )


def compute_exploratory_measurements(
    front_detection: PoseDetectionResult,
    front_scale: ScaleCalibrationResult,
) -> Tuple[Optional[ExploratoryMeasurement], Optional[ExploratoryMeasurement]]:
    """Compute exploratory shoulder width (biacromial) and inseam (crotch to ankle)."""
    w_px = front_detection.image_width
    h_px = front_detection.image_height

    # 1. Shoulder width: distance between left and right shoulders
    left_sh = front_detection.get_landmark(PoseLandmarkIndex.LEFT_SHOULDER)
    right_sh = front_detection.get_landmark(PoseLandmarkIndex.RIGHT_SHOULDER)

    shoulder_measurement = None
    if left_sh is not None and right_sh is not None:
        dx = abs(left_sh.x - right_sh.x) * w_px
        dy = abs(left_sh.y - right_sh.y) * h_px
        shoulder_span_px = math.hypot(dx, dy)
        shoulder_width_cm = round(shoulder_span_px * front_scale.cm_per_pixel, 2)
        shoulder_measurement = ExploratoryMeasurement(
            name="shoulder_width",
            value_cm=shoulder_width_cm,
            pixel_span=round(shoulder_span_px, 1),
            is_valid=True,
            is_exploratory=True,
            notes="Biacromial distance between shoulder landmarks.",
        )

    # 2. Inseam: vertical distance from crotch level to ankle level
    left_hip = front_detection.get_landmark(PoseLandmarkIndex.LEFT_HIP)
    right_hip = front_detection.get_landmark(PoseLandmarkIndex.RIGHT_HIP)
    left_ankle = front_detection.get_landmark(PoseLandmarkIndex.LEFT_ANKLE)
    right_ankle = front_detection.get_landmark(PoseLandmarkIndex.RIGHT_ANKLE)

    inseam_measurement = None
    if None not in (left_hip, right_hip, left_ankle, right_ankle):
        mid_hip_y = ((left_hip.y + right_hip.y) / 2.0) * h_px
        mid_ankle_y = ((left_ankle.y + right_ankle.y) / 2.0) * h_px
        # Approximate perineum / crotch ~ 8% of leg length below mid-hip
        leg_span = mid_ankle_y - mid_hip_y
        crotch_y = mid_hip_y + 0.08 * leg_span
        inseam_span_px = max(0.0, mid_ankle_y - crotch_y)
        inseam_cm = round(inseam_span_px * front_scale.cm_per_pixel, 2)
        inseam_measurement = ExploratoryMeasurement(
            name="inseam",
            value_cm=inseam_cm,
            pixel_span=round(inseam_span_px, 1),
            is_valid=True,
            is_exploratory=True,
            notes="Perineum to medial malleolus vertical distance.",
        )

    return shoulder_measurement, inseam_measurement


def compute_body_measurements(
    front_detection: PoseDetectionResult,
    front_mask: np.ndarray,
    front_scale: ScaleCalibrationResult,
    side_detection: PoseDetectionResult,
    side_mask: np.ndarray,
    side_scale: ScaleCalibrationResult,
    include_exploratory: bool = True,
) -> GeometricMeasurementResult:
    """
    End-to-end geometric measurement pipeline on a paired front and side image.

    Args:
        front_detection: Pose detection outputs for front photo.
        front_mask: Binary uint8 segmentation mask for front photo.
        front_scale: Calibrated scale for front photo.
        side_detection: Pose detection outputs for side photo.
        side_mask: Binary uint8 segmentation mask for side photo.
        side_scale: Calibrated scale for side photo.
        include_exploratory: Whether to compute shoulder width and inseam.

    Returns:
        GeometricMeasurementResult with chest, waist, hip, and exploratory measurements.
    """
    rejections: List[str] = []

    # Validate scale calibrations
    if not front_scale.is_valid:
        rejections.extend([f"FRONT_SCALE_{r}" for r in front_scale.rejection_reasons])
    if not side_scale.is_valid:
        rejections.extend([f"SIDE_SCALE_{r}" for r in side_scale.rejection_reasons])

    if rejections:
        # Structured failure placeholder
        dummy_cs = lambda name: CrossSectionMeasurement(
            name=name, front_y_px=0, side_y_px=0, width_px=0, depth_px=0,
            width_cm=0.0, depth_cm=0.0, circumference_cm=0.0,
            is_valid=False, rejection_reason="Scale calibration failed.",
        )
        return GeometricMeasurementResult(
            chest=dummy_cs("chest"),
            waist=dummy_cs("waist"),
            hip=dummy_cs("hip"),
            is_valid=False,
            rejection_reasons=rejections,
        )

    # Locate measurement levels
    try:
        levels = locate_cross_section_levels(
            front_detection=front_detection,
            front_mask=front_mask,
            side_detection=side_detection,
            side_mask=side_mask,
        )
    except Exception as e:
        rejections.append(f"LEVEL_MAPPING_FAILED: {e}")
        dummy_cs = lambda name: CrossSectionMeasurement(
            name=name, front_y_px=0, side_y_px=0, width_px=0, depth_px=0,
            width_cm=0.0, depth_cm=0.0, circumference_cm=0.0,
            is_valid=False, rejection_reason=str(e),
        )
        return GeometricMeasurementResult(
            chest=dummy_cs("chest"),
            waist=dummy_cs("waist"),
            hip=dummy_cs("hip"),
            is_valid=False,
            rejection_reasons=rejections,
        )

    # Compute primary circumferences
    chest = compute_cross_section(
        name="chest",
        front_y_px=levels["chest"][0],
        side_y_px=levels["chest"][1],
        front_mask=front_mask,
        side_mask=side_mask,
        front_scale=front_scale,
        side_scale=side_scale,
    )
    waist = compute_cross_section(
        name="waist",
        front_y_px=levels["waist"][0],
        side_y_px=levels["waist"][1],
        front_mask=front_mask,
        side_mask=side_mask,
        front_scale=front_scale,
        side_scale=side_scale,
    )
    hip = compute_cross_section(
        name="hip",
        front_y_px=levels["hip"][0],
        side_y_px=levels["hip"][1],
        front_mask=front_mask,
        side_mask=side_mask,
        front_scale=front_scale,
        side_scale=side_scale,
    )

    for cs in (chest, waist, hip):
        if not cs.is_valid:
            rejections.append(f"{cs.name.upper()}_INVALID: {cs.rejection_reason}")

    # Exploratory measurements
    shoulder_m, inseam_m = (None, None)
    if include_exploratory:
        shoulder_m, inseam_m = compute_exploratory_measurements(
            front_detection=front_detection,
            front_scale=front_scale,
        )

    is_valid = len(rejections) == 0

    return GeometricMeasurementResult(
        chest=chest,
        waist=waist,
        hip=hip,
        shoulder_width=shoulder_m,
        inseam=inseam_m,
        is_valid=is_valid,
        rejection_reasons=rejections,
    )
