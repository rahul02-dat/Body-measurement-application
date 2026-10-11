"""Unit tests for pose quality evaluation and failure reasons."""

import pytest

from body_measurement.pose_detection import LandmarkPoint, PoseDetectionResult, PoseLandmarkIndex
from body_measurement.quality_checks import evaluate_pose_quality


@pytest.fixture
def mock_valid_detection():
    """Build a complete, well-framed 33-landmark pose detection result."""
    landmarks = []
    for i in range(33):
        # Default positioning with good visibility
        # Head around y = 0.15, shoulders at y = 0.25, hips at y = 0.5, feet at y = 0.90
        if i in [0, 1, 2, 3, 4, 5, 6, 7, 8]:  # Head
            y = 0.15
        elif i in [11, 12]:  # Shoulders
            y = 0.25
        elif i in [23, 24]:  # Hips
            y = 0.50
        elif i in [27, 28, 29, 30, 31, 32]:  # Feet / Ankles
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
                visibility=0.9,
                presence=0.9,
            )
        )

    return PoseDetectionResult(
        has_pose=True,
        num_poses_detected=1,
        landmarks=landmarks,
        image_width=640,
        image_height=480,
    )


def test_evaluate_valid_pose(mock_valid_detection):
    """Verify well-framed pose produces is_valid=True with no rejection reasons."""
    report = evaluate_pose_quality(mock_valid_detection)
    assert report.is_valid is True
    assert len(report.rejection_reasons) == 0
    assert report.head_visible is True
    assert report.feet_visible is True
    assert report.torso_visible is True
    assert report.mean_landmark_visibility >= 0.8


def test_reject_no_person_detected():
    """Verify detection without a pose is rejected with NO_PERSON_DETECTED."""
    empty_det = PoseDetectionResult(has_pose=False, num_poses_detected=0)
    report = evaluate_pose_quality(empty_det)
    assert report.is_valid is False
    assert "NO_PERSON_DETECTED" in report.rejection_reasons


def test_reject_multiple_people(mock_valid_detection):
    """Verify frames with multiple detected people are rejected."""
    mock_valid_detection.num_poses_detected = 2
    report = evaluate_pose_quality(mock_valid_detection)
    assert report.is_valid is False
    assert "MULTIPLE_PEOPLE_DETECTED" in report.rejection_reasons


def test_reject_head_cropped_at_top(mock_valid_detection):
    """Verify person with head too close to top edge is rejected."""
    # Move nose to y = 0.005 (too close to top margin)
    landmarks = list(mock_valid_detection.landmarks)
    landmarks[PoseLandmarkIndex.NOSE] = LandmarkPoint(
        index=0, name="NOSE", x=0.5, y=0.005, z=0.0, visibility=0.9, presence=0.9
    )
    mock_valid_detection.landmarks = landmarks

    report = evaluate_pose_quality(mock_valid_detection, border_margin_fraction=0.02)
    assert report.is_valid is False
    assert "HEAD_CROPPED_AT_TOP" in report.rejection_reasons


def test_reject_feet_cropped_at_bottom(mock_valid_detection):
    """Verify person with feet touching or exceeding bottom boundary is rejected."""
    # Move ankle/foot to y = 0.995 (exceeds bottom margin)
    landmarks = list(mock_valid_detection.landmarks)
    landmarks[PoseLandmarkIndex.LEFT_FOOT_INDEX] = LandmarkPoint(
        index=31, name="LEFT_FOOT_INDEX", x=0.5, y=0.995, z=0.0, visibility=0.9, presence=0.9
    )
    mock_valid_detection.landmarks = landmarks

    report = evaluate_pose_quality(mock_valid_detection, border_margin_fraction=0.02)
    assert report.is_valid is False
    assert "FEET_CROPPED_AT_BOTTOM" in report.rejection_reasons


def test_reject_low_landmark_confidence(mock_valid_detection):
    """Verify low average visibility produces LOW_LANDMARK_CONFIDENCE."""
    # Lower visibility of all landmarks to 0.2
    low_vis_landmarks = [
        LandmarkPoint(lm.index, lm.name, lm.x, lm.y, lm.z, visibility=0.2, presence=0.2)
        for lm in mock_valid_detection.landmarks
    ]
    mock_valid_detection.landmarks = low_vis_landmarks

    report = evaluate_pose_quality(mock_valid_detection, min_mean_visibility=0.5)
    assert report.is_valid is False
    assert "LOW_LANDMARK_CONFIDENCE" in report.rejection_reasons


def test_reject_torso_occluded(mock_valid_detection):
    """Verify low visibility on hips/shoulders produces TORSO_OCCLUDED_OR_LOW_VISIBILITY."""
    landmarks = list(mock_valid_detection.landmarks)
    # Occlude left and right hips
    landmarks[PoseLandmarkIndex.LEFT_HIP] = LandmarkPoint(
        index=23, name="LEFT_HIP", x=0.5, y=0.5, z=0.0, visibility=0.1, presence=0.1
    )
    landmarks[PoseLandmarkIndex.RIGHT_HIP] = LandmarkPoint(
        index=24, name="RIGHT_HIP", x=0.5, y=0.5, z=0.0, visibility=0.1, presence=0.1
    )
    mock_valid_detection.landmarks = landmarks

    report = evaluate_pose_quality(mock_valid_detection)
    assert report.is_valid is False
    assert "TORSO_OCCLUDED_OR_LOW_VISIBILITY" in report.rejection_reasons
