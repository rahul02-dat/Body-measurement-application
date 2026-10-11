"""Unit and integration tests for MediaPipe PoseDetector."""

from pathlib import Path
import numpy as np
import pytest

from body_measurement.image_io import LoadedImage
from body_measurement.pose_detection import PoseDetector, PoseLandmarkIndex


def test_pose_detector_missing_model():
    """Verify initializing detector with invalid path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        PoseDetector(model_asset_path="nonexistent_model.task")


def test_pose_detector_blank_image():
    """Verify running detector on blank black image returns structured empty result without errors."""
    model_path = Path(__file__).parent.parent / "models" / "pose_landmarker_full.task"
    if not model_path.is_file():
        pytest.skip("Model binary not found")

    with PoseDetector(model_asset_path=model_path) as detector:
        blank_img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(blank_img)

        assert result.has_pose is False
        assert result.num_poses_detected == 0
        assert len(result.landmarks) == 0
        assert result.image_width == 640
        assert result.image_height == 480


def test_pose_detector_with_loaded_image():
    """Verify detect accepts a LoadedImage dataclass."""
    model_path = Path(__file__).parent.parent / "models" / "pose_landmarker_full.task"
    if not model_path.is_file():
        pytest.skip("Model binary not found")

    with PoseDetector(model_asset_path=model_path) as detector:
        dummy_array = np.full((300, 300, 3), 128, dtype=np.uint8)
        loaded = LoadedImage(
            path=Path("dummy.jpg"),
            rgb_array=dummy_array,
            width=300,
            height=300,
            channels=3,
        )
        result = detector.detect(loaded)
        assert result.image_width == 300
        assert result.image_height == 300


def test_pose_landmark_indices_coverage():
    """Verify key anatomical landmark enum indices."""
    assert PoseLandmarkIndex.NOSE == 0
    assert PoseLandmarkIndex.LEFT_SHOULDER == 11
    assert PoseLandmarkIndex.RIGHT_SHOULDER == 12
    assert PoseLandmarkIndex.LEFT_HIP == 23
    assert PoseLandmarkIndex.RIGHT_HIP == 24
    assert PoseLandmarkIndex.LEFT_ANKLE == 27
    assert PoseLandmarkIndex.RIGHT_ANKLE == 28
    assert PoseLandmarkIndex.RIGHT_FOOT_INDEX == 32
