"""Pose quality assessment, landmark confidence checks, and structured rejection rules."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from body_measurement.pose_detection import PoseDetectionResult, PoseLandmarkIndex


@dataclass
class PoseQualityReport:
    """Structured quality report detailing validation outcome and explicit rejection reasons."""

    is_valid: bool
    rejection_reasons: List[str] = field(default_factory=list)
    num_poses_detected: int = 0
    mean_landmark_visibility: float = 0.0
    mean_landmark_presence: float = 0.0
    head_visible: bool = False
    feet_visible: bool = False
    torso_visible: bool = False
    top_margin_fraction: float = 0.0
    bottom_margin_fraction: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


def evaluate_pose_quality(
    detection: PoseDetectionResult,
    min_mean_visibility: float = 0.5,
    min_keypoint_visibility: float = 0.4,
    border_margin_fraction: float = 0.015,
) -> PoseQualityReport:
    """
    Evaluate pose detection quality and frame composition.

    Checks:
    1. Person presence (exactly 1 person required).
    2. Multiple people rejection.
    3. Head visibility and top boundary margin (detect head cropping).
    4. Feet visibility and bottom boundary margin (detect feet cropping).
    5. Torso visibility (shoulders and hips must be present and visible).
    6. Overall landmark confidence (mean visibility).

    Args:
        detection: PoseDetectionResult from PoseDetector.
        min_mean_visibility: Minimum allowable average visibility across all landmarks.
        min_keypoint_visibility: Minimum visibility required for individual essential landmarks.
        border_margin_fraction: Margin threshold to detect top/bottom cropping.

    Returns:
        Structured PoseQualityReport with is_valid boolean and explicit rejection reason codes.
    """
    rejection_reasons: List[str] = []
    details: Dict[str, Any] = {}

    # Check 1 & 2: Pose presence and multiplicity
    if not detection.has_pose or detection.num_poses_detected == 0:
        return PoseQualityReport(
            is_valid=False,
            rejection_reasons=["NO_PERSON_DETECTED"],
            details={"message": "MediaPipe Pose Landmarker found no human pose in frame."},
        )

    if detection.num_poses_detected > 1:
        rejection_reasons.append("MULTIPLE_PEOPLE_DETECTED")
        details["num_poses_detected"] = detection.num_poses_detected

    landmarks = detection.landmarks
    if len(landmarks) < 33:
        rejection_reasons.append("INCOMPLETE_LANDMARK_SET")
        return PoseQualityReport(
            is_valid=False,
            rejection_reasons=rejection_reasons,
            num_poses_detected=detection.num_poses_detected,
            details=details,
        )

    # Compute overall landmark confidence
    visibilities = [lm.visibility for lm in landmarks]
    presences = [lm.presence for lm in landmarks]
    mean_vis = float(sum(visibilities) / len(visibilities))
    mean_pres = float(sum(presences) / len(presences))

    details["mean_visibility"] = round(mean_vis, 3)
    details["mean_presence"] = round(mean_pres, 3)

    if mean_vis < min_mean_visibility:
        rejection_reasons.append("LOW_LANDMARK_CONFIDENCE")

    # Check 3: Head landmarks & top frame margin
    head_indices = [
        PoseLandmarkIndex.NOSE,
        PoseLandmarkIndex.LEFT_EYE,
        PoseLandmarkIndex.RIGHT_EYE,
        PoseLandmarkIndex.LEFT_EAR,
        PoseLandmarkIndex.RIGHT_EAR,
    ]
    head_lms = [detection.get_landmark(idx) for idx in head_indices]
    head_visible = any(lm is not None and lm.visibility >= min_keypoint_visibility for lm in head_lms)

    # Top margin check (minimum y of head landmarks)
    head_y_vals = [lm.y for lm in head_lms if lm is not None]
    min_head_y = min(head_y_vals) if head_y_vals else 0.0
    top_margin = max(0.0, min_head_y)

    if not head_visible:
        rejection_reasons.append("HEAD_NOT_VISIBLE")
    elif min_head_y < border_margin_fraction:
        rejection_reasons.append("HEAD_CROPPED_AT_TOP")
        details["min_head_y"] = round(min_head_y, 4)

    # Check 4: Feet landmarks & bottom frame margin
    feet_indices = [
        PoseLandmarkIndex.LEFT_ANKLE,
        PoseLandmarkIndex.RIGHT_ANKLE,
        PoseLandmarkIndex.LEFT_HEEL,
        PoseLandmarkIndex.RIGHT_HEEL,
        PoseLandmarkIndex.LEFT_FOOT_INDEX,
        PoseLandmarkIndex.RIGHT_FOOT_INDEX,
    ]
    feet_lms = [detection.get_landmark(idx) for idx in feet_indices]
    feet_visible = any(lm is not None and lm.visibility >= min_keypoint_visibility for lm in feet_lms)

    feet_y_vals = [lm.y for lm in feet_lms if lm is not None]
    max_feet_y = max(feet_y_vals) if feet_y_vals else 1.0
    bottom_margin = max(0.0, 1.0 - max_feet_y)

    if not feet_visible:
        rejection_reasons.append("FEET_NOT_VISIBLE")
    elif max_feet_y > (1.0 - border_margin_fraction):
        rejection_reasons.append("FEET_CROPPED_AT_BOTTOM")
        details["max_feet_y"] = round(max_feet_y, 4)

    # Check 5: Torso anchors (shoulders and hips)
    left_shoulder = detection.get_landmark(PoseLandmarkIndex.LEFT_SHOULDER)
    right_shoulder = detection.get_landmark(PoseLandmarkIndex.RIGHT_SHOULDER)
    left_hip = detection.get_landmark(PoseLandmarkIndex.LEFT_HIP)
    right_hip = detection.get_landmark(PoseLandmarkIndex.RIGHT_HIP)

    torso_lms = [left_shoulder, right_shoulder, left_hip, right_hip]
    torso_vis = [lm.visibility for lm in torso_lms if lm is not None]
    torso_visible = len(torso_vis) == 4 and all(v >= min_keypoint_visibility for v in torso_vis)

    if not torso_visible:
        rejection_reasons.append("TORSO_OCCLUDED_OR_LOW_VISIBILITY")

    is_valid = len(rejection_reasons) == 0

    return PoseQualityReport(
        is_valid=is_valid,
        rejection_reasons=rejection_reasons,
        num_poses_detected=detection.num_poses_detected,
        mean_landmark_visibility=round(mean_vis, 4),
        mean_landmark_presence=round(mean_pres, 4),
        head_visible=head_visible,
        feet_visible=feet_visible,
        torso_visible=torso_visible,
        top_margin_fraction=round(top_margin, 4),
        bottom_margin_fraction=round(bottom_margin, 4),
        details=details,
    )
