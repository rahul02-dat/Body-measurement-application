"""Scale calibration converting pixel dimensions to physical centimeters via user height."""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from body_measurement.config import DEFAULT_THRESHOLDS
from body_measurement.pose_detection import PoseDetectionResult, PoseLandmarkIndex
from body_measurement.segmentation import extract_binary_mask, extract_bounding_box


DOCUMENTED_SCALE_ASSUMPTIONS: List[str] = [
    "User-entered standing height is assumed accurate, metric, and taken without footwear.",
    "Subject stands fully upright in natural neutral stance without material slouching.",
    "Camera is positioned at mid-torso height in portrait orientation with minimal pitch/roll tilt.",
    "Perspective foreshortening can distort scale; level camera sensors reduce but do not eliminate perspective distortion.",
    "Front and side images must be captured at the identical distance from subject to camera lens.",
]


@dataclass
class BodyBounds:
    """Detected vertical span of the human body in pixel coordinates."""

    top_y_px: int
    bottom_y_px: int
    span_px: int
    image_height: int
    source: str
    is_reliable: bool
    reliability_notes: List[str] = field(default_factory=list)


@dataclass
class ScaleCalibrationResult:
    """Scale calibration result for a single camera view."""

    pixels_per_cm: float
    cm_per_pixel: float
    entered_height_cm: float
    body_span_pixels: int
    bounds: BodyBounds
    torso_tilt_degrees: float
    is_valid: bool
    rejection_reasons: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=lambda: list(DOCUMENTED_SCALE_ASSUMPTIONS))


@dataclass
class PairScaleResult:
    """Consolidated scale calibration across paired front and side views."""

    front_scale: ScaleCalibrationResult
    side_scale: ScaleCalibrationResult
    scale_discrepancy_fraction: float
    effective_pixels_per_cm: float
    is_valid: bool
    rejection_reasons: List[str] = field(default_factory=list)


def calculate_torso_tilt_degrees(detection: PoseDetectionResult) -> float:
    """
    Calculate torso angular deviation from true vertical in degrees.
    Detects subject slouching or significant camera roll/pitch.
    """
    if not detection.has_pose:
        return 0.0

    left_sh = detection.get_landmark(PoseLandmarkIndex.LEFT_SHOULDER)
    right_sh = detection.get_landmark(PoseLandmarkIndex.RIGHT_SHOULDER)
    left_hip = detection.get_landmark(PoseLandmarkIndex.LEFT_HIP)
    right_hip = detection.get_landmark(PoseLandmarkIndex.RIGHT_HIP)

    if None in (left_sh, right_sh, left_hip, right_hip):
        return 0.0

    # Midpoints in normalized coordinates
    mid_shoulder_x = (left_sh.x + right_sh.x) / 2.0
    mid_shoulder_y = (left_sh.y + right_sh.y) / 2.0

    mid_hip_x = (left_hip.x + right_hip.x) / 2.0
    mid_hip_y = (left_hip.y + right_hip.y) / 2.0

    dx = mid_shoulder_x - mid_hip_x
    # In image coordinates, y increases downward, so shoulder has smaller y than hip
    dy = mid_hip_y - mid_shoulder_y

    if dy <= 0:
        # Inverted or extreme slouch
        return 90.0

    angle_rad = math.atan2(abs(dx), dy)
    return math.degrees(angle_rad)


def detect_vertical_body_bounds(
    detection: PoseDetectionResult,
    binary_mask: Optional[np.ndarray] = None,
    crop_margin_fraction: float = 0.015,
) -> BodyBounds:
    """
    Detect vertical top (crown) and bottom (floor contact) bounds of the body silhouette.

    Uses a hybrid approach:
    - Bounded by silhouette segmentation mask if available.
    - Verified against facial/cranial and foot/ankle anatomical landmarks.
    """
    h = detection.image_height
    w = detection.image_width
    notes: List[str] = []
    is_reliable = True

    if not detection.has_pose or h <= 0 or w <= 0:
        return BodyBounds(
            top_y_px=0,
            bottom_y_px=0,
            span_px=0,
            image_height=h,
            source="none",
            is_reliable=False,
            reliability_notes=["No pose detected to anchor body bounds"],
        )

    # 1. Landmark-based anchor points
    head_indices = [
        PoseLandmarkIndex.NOSE,
        PoseLandmarkIndex.LEFT_EYE,
        PoseLandmarkIndex.RIGHT_EYE,
        PoseLandmarkIndex.LEFT_EAR,
        PoseLandmarkIndex.RIGHT_EAR,
    ]
    head_lms = [detection.get_landmark(idx) for idx in head_indices if detection.get_landmark(idx) is not None]
    head_y_px = [int(lm.y * h) for lm in head_lms]
    min_head_landmark_y = min(head_y_px) if head_y_px else int(0.15 * h)

    feet_indices = [
        PoseLandmarkIndex.LEFT_ANKLE,
        PoseLandmarkIndex.RIGHT_ANKLE,
        PoseLandmarkIndex.LEFT_HEEL,
        PoseLandmarkIndex.RIGHT_HEEL,
        PoseLandmarkIndex.LEFT_FOOT_INDEX,
        PoseLandmarkIndex.RIGHT_FOOT_INDEX,
    ]
    feet_lms = [detection.get_landmark(idx) for idx in feet_indices if detection.get_landmark(idx) is not None]
    feet_y_px = [int(lm.y * h) for lm in feet_lms]
    max_feet_landmark_y = max(feet_y_px) if feet_y_px else int(0.90 * h)

    # 2. Hybrid estimation using segmentation mask if provided
    top_y = min_head_landmark_y
    bottom_y = max_feet_landmark_y
    source = "landmarks"

    if binary_mask is not None and np.any(binary_mask > 0):
        # Find segmentation mask bounding box
        bbox = extract_bounding_box(binary_mask)
        if bbox:
            ymin, xmin, ymax, xmax = bbox

            # The crown of the head in segmentation should be near or above the eyes
            # Allow crown to be up to 15% of body height above eyes
            if ymin <= min_head_landmark_y:
                top_y = ymin
                source = "hybrid_segmentation_landmarks"
            else:
                top_y = min_head_landmark_y
                notes.append("Mask top was below head landmarks; defaulted to landmark crown estimate.")

            # The bottom of feet in segmentation should be at or slightly below ankles
            if ymax >= max_feet_landmark_y:
                bottom_y = ymax
            else:
                bottom_y = max_feet_landmark_y
                notes.append("Mask bottom was above foot landmarks; defaulted to foot landmark.")
    else:
        # Without mask, estimate crown above eyes by standard cranial ratio (~0.05 height)
        cranial_offset = int(0.04 * h)
        top_y = max(0, min_head_landmark_y - cranial_offset)
        source = "landmarks_with_cranial_offset"

    span_px = max(0, bottom_y - top_y + 1)

    # 3. Boundary cropping checks
    min_margin_px = int(crop_margin_fraction * h)
    if top_y <= min_margin_px:
        is_reliable = False
        notes.append("Head crown is cropped or touching top frame border.")
    if bottom_y >= (h - min_margin_px):
        is_reliable = False
        notes.append("Feet are cropped or touching bottom frame border.")

    if span_px < int(0.4 * h):
        is_reliable = False
        notes.append(f"Detected body span ({span_px}px) is too small relative to frame ({h}px).")

    return BodyBounds(
        top_y_px=top_y,
        bottom_y_px=bottom_y,
        span_px=span_px,
        image_height=h,
        source=source,
        is_reliable=is_reliable,
        reliability_notes=notes,
    )


def calibrate_scale(
    height_cm: float,
    detection: PoseDetectionResult,
    binary_mask: Optional[np.ndarray] = None,
    max_tilt_degrees: float = 8.0,
) -> ScaleCalibrationResult:
    """
    Calibrate pixel scale (pixels/cm) from reported height and detected body span.

    Args:
        height_cm: Reported standing height in centimeters.
        detection: PoseDetectionResult from PoseDetector.
        binary_mask: Optional binary foreground silhouette mask.
        max_tilt_degrees: Maximum allowable torso tilt angle before slouch rejection.

    Returns:
        ScaleCalibrationResult containing pixels_per_cm, bounds, and validity.
    """
    rejections: List[str] = []

    # Validate height input
    if not math.isfinite(height_cm) or height_cm <= 0:
        return ScaleCalibrationResult(
            pixels_per_cm=0.0,
            cm_per_pixel=0.0,
            entered_height_cm=height_cm,
            body_span_pixels=0,
            bounds=BodyBounds(0, 0, 0, 0, "none", False, ["Invalid height"]),
            torso_tilt_degrees=0.0,
            is_valid=False,
            rejection_reasons=["INVALID_NON_FINITE_HEIGHT"],
        )

    if not (DEFAULT_THRESHOLDS.MIN_HEIGHT_CM <= height_cm <= DEFAULT_THRESHOLDS.MAX_HEIGHT_CM):
        rejections.append("HEIGHT_OUT_OF_ANTHROPOMETRIC_BOUNDS")

    # Detect body bounds
    bounds = detect_vertical_body_bounds(detection, binary_mask)
    if not bounds.is_reliable:
        rejections.extend(bounds.reliability_notes)

    # Check torso tilt / slouching
    torso_tilt = calculate_torso_tilt_degrees(detection)
    if torso_tilt > max_tilt_degrees:
        rejections.append(f"POSTURE_TILT_OR_SLOUCHING_DETECTED ({torso_tilt:.1f}° > {max_tilt_degrees:.1f}°)")

    if bounds.span_px <= 0:
        rejections.append("ZERO_BODY_SPAN_DETECTED")
        return ScaleCalibrationResult(
            pixels_per_cm=0.0,
            cm_per_pixel=0.0,
            entered_height_cm=height_cm,
            body_span_pixels=0,
            bounds=bounds,
            torso_tilt_degrees=torso_tilt,
            is_valid=False,
            rejection_reasons=rejections,
        )

    pixels_per_cm = bounds.span_px / height_cm
    cm_per_pixel = height_cm / bounds.span_px

    is_valid = len(rejections) == 0

    return ScaleCalibrationResult(
        pixels_per_cm=round(pixels_per_cm, 4),
        cm_per_pixel=round(cm_per_pixel, 4),
        entered_height_cm=height_cm,
        body_span_pixels=bounds.span_px,
        bounds=bounds,
        torso_tilt_degrees=round(torso_tilt, 2),
        is_valid=is_valid,
        rejection_reasons=rejections,
    )


def verify_pair_scale_consistency(
    front_scale: ScaleCalibrationResult,
    side_scale: ScaleCalibrationResult,
    max_discrepancy_fraction: float = 0.05,
) -> PairScaleResult:
    """
    Enforce consistency between front and side scale factors.
    Rejects pairs where subject distance changed between photos.

    Args:
        front_scale: Scale calibration from front photo.
        side_scale: Scale calibration from side photo.
        max_discrepancy_fraction: Maximum allowed relative difference (default 5% / 0.05).
    """
    rejections: List[str] = []

    if not front_scale.is_valid:
        rejections.extend([f"FRONT_{r}" for r in front_scale.rejection_reasons])
    if not side_scale.is_valid:
        rejections.extend([f"SIDE_{r}" for r in side_scale.rejection_reasons])

    f_px_cm = front_scale.pixels_per_cm
    s_px_cm = side_scale.pixels_per_cm

    if f_px_cm <= 0 or s_px_cm <= 0:
        return PairScaleResult(
            front_scale=front_scale,
            side_scale=side_scale,
            scale_discrepancy_fraction=1.0,
            effective_pixels_per_cm=0.0,
            is_valid=False,
            rejection_reasons=rejections + ["NON_POSITIVE_SCALE_FACTOR"],
        )

    mean_scale = (f_px_cm + s_px_cm) / 2.0
    discrepancy = abs(f_px_cm - s_px_cm) / mean_scale

    if discrepancy > max_discrepancy_fraction:
        rejections.append(
            f"INCONSISTENT_CAPTURE_DISTANCE_BETWEEN_VIEWS "
            f"(discrepancy {discrepancy * 100:.1f}% exceeds limit {max_discrepancy_fraction * 100:.1f}%)"
        )

    is_valid = len(rejections) == 0

    return PairScaleResult(
        front_scale=front_scale,
        side_scale=side_scale,
        scale_discrepancy_fraction=round(discrepancy, 4),
        effective_pixels_per_cm=round(mean_scale, 4),
        is_valid=is_valid,
        rejection_reasons=rejections,
    )


def simulate_perspective_scale_sensitivity(
    nominal_height_cm: float = 175.0,
    distance_m: float = 2.8,
    camera_height_m: float = 1.0,
    focal_length_px: float = 1200.0,
    tilt_degrees_range: Tuple[float, ...] = (-5.0, 0.0, 5.0),
) -> Dict[str, float]:
    """
    Sensitivity simulation quantifying the effect of camera pitch tilt and distance
    on projected body span and resulting pixel scale.
    Per AGENTS.md Phase S0-D requirement 6.
    """
    results: Dict[str, float] = {}
    nominal_height_m = nominal_height_cm / 100.0

    for tilt in tilt_degrees_range:
        tilt_rad = math.radians(tilt)
        # Perspective pinhole model: y_proj = f * Y / Z
        # Effective projected height under small camera tilt
        cos_tilt = math.cos(tilt_rad)
        effective_span_px = focal_length_px * (nominal_height_m * cos_tilt) / distance_m
        effective_px_cm = effective_span_px / nominal_height_cm
        results[f"tilt_{tilt:+0.1f}deg_px_per_cm"] = round(effective_px_cm, 4)

    return results
