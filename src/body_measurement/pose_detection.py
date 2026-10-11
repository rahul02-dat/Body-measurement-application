"""MediaPipe Pose Landmarker wrapper and landmark data models."""

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import List, Optional, Tuple, Union

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from body_measurement.image_io import LoadedImage


class PoseLandmarkIndex(IntEnum):
    """Standard MediaPipe Pose landmark indices (33 landmarks)."""

    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32


# Standard anatomical skeletal connections for diagnostic visualization
POSE_CONNECTIONS: List[Tuple[PoseLandmarkIndex, PoseLandmarkIndex]] = [
    # Torso
    (PoseLandmarkIndex.LEFT_SHOULDER, PoseLandmarkIndex.RIGHT_SHOULDER),
    (PoseLandmarkIndex.LEFT_SHOULDER, PoseLandmarkIndex.LEFT_HIP),
    (PoseLandmarkIndex.RIGHT_SHOULDER, PoseLandmarkIndex.RIGHT_HIP),
    (PoseLandmarkIndex.LEFT_HIP, PoseLandmarkIndex.RIGHT_HIP),
    # Left Arm
    (PoseLandmarkIndex.LEFT_SHOULDER, PoseLandmarkIndex.LEFT_ELBOW),
    (PoseLandmarkIndex.LEFT_ELBOW, PoseLandmarkIndex.LEFT_WRIST),
    # Right Arm
    (PoseLandmarkIndex.RIGHT_SHOULDER, PoseLandmarkIndex.RIGHT_ELBOW),
    (PoseLandmarkIndex.RIGHT_ELBOW, PoseLandmarkIndex.RIGHT_WRIST),
    # Left Leg
    (PoseLandmarkIndex.LEFT_HIP, PoseLandmarkIndex.LEFT_KNEE),
    (PoseLandmarkIndex.LEFT_KNEE, PoseLandmarkIndex.LEFT_ANKLE),
    (PoseLandmarkIndex.LEFT_ANKLE, PoseLandmarkIndex.LEFT_HEEL),
    (PoseLandmarkIndex.LEFT_HEEL, PoseLandmarkIndex.LEFT_FOOT_INDEX),
    (PoseLandmarkIndex.LEFT_ANKLE, PoseLandmarkIndex.LEFT_FOOT_INDEX),
    # Right Leg
    (PoseLandmarkIndex.RIGHT_HIP, PoseLandmarkIndex.RIGHT_KNEE),
    (PoseLandmarkIndex.RIGHT_KNEE, PoseLandmarkIndex.RIGHT_ANKLE),
    (PoseLandmarkIndex.RIGHT_ANKLE, PoseLandmarkIndex.RIGHT_HEEL),
    (PoseLandmarkIndex.RIGHT_HEEL, PoseLandmarkIndex.RIGHT_FOOT_INDEX),
    (PoseLandmarkIndex.RIGHT_ANKLE, PoseLandmarkIndex.RIGHT_FOOT_INDEX),
]


@dataclass(frozen=True)
class LandmarkPoint:
    """A single detected anatomical landmark with coordinates and confidence values."""

    index: int
    name: str
    x: float
    y: float
    z: float
    visibility: float = 1.0
    presence: float = 1.0


@dataclass
class PoseDetectionResult:
    """Structured outputs from pose detection and segmentation."""

    has_pose: bool
    num_poses_detected: int = 0
    # Normalized coordinates in [0.0, 1.0] relative to image width and height
    landmarks: List[LandmarkPoint] = field(default_factory=list)
    # 3D coordinates in meters relative to mid-hip center
    # NOTE per AGENTS.md Rule 7: These are model coordinate outputs, NOT ground truth metric measurements.
    world_landmarks: List[LandmarkPoint] = field(default_factory=list)
    # Raw float segmentation mask (values in [0.0, 1.0])
    segmentation_mask: Optional[np.ndarray] = None
    image_width: int = 0
    image_height: int = 0

    def get_landmark(self, index: Union[int, PoseLandmarkIndex]) -> Optional[LandmarkPoint]:
        """Retrieve a specific landmark by index."""
        target_idx = int(index)
        for lm in self.landmarks:
            if lm.index == target_idx:
                return lm
        return None


class PoseDetector:
    """Wrapper around MediaPipe Pose Landmarker with image input and mask extraction."""

    def __init__(
        self,
        model_asset_path: Union[str, Path] = "models/pose_landmarker_full.task",
        min_detection_confidence: float = 0.5,
        min_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        output_segmentation_masks: bool = True,
        max_num_poses: int = 2,
    ):
        self.model_path = Path(model_asset_path)
        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"MediaPipe model file not found at: {self.model_path}. "
                "Download it via `curl -o models/pose_landmarker_full.task ...`"
            )

        self.min_detection_confidence = min_detection_confidence
        self.min_presence_confidence = min_presence_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.output_segmentation_masks = output_segmentation_masks
        self.max_num_poses = max_num_poses

        base_options = python.BaseOptions(model_asset_path=str(self.model_path))
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            output_segmentation_masks=output_segmentation_masks,
            num_poses=max_num_poses,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Release underlying MediaPipe landmarker resources."""
        if hasattr(self, "_landmarker") and self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

    def detect(self, image: Union[LoadedImage, np.ndarray]) -> PoseDetectionResult:
        """
        Run pose detection and optional segmentation on an RGB image.

        Args:
            image: LoadedImage or uint8 RGB numpy array of shape (H, W, 3).

        Returns:
            PoseDetectionResult with landmarks and segmentation mask.
        """
        if isinstance(image, LoadedImage):
            rgb_array = image.rgb_array
            height, width = image.height, image.width
        elif isinstance(image, np.ndarray):
            rgb_array = image
            height, width = rgb_array.shape[:2]
        else:
            raise TypeError(f"Expected LoadedImage or np.ndarray, got {type(image)}")

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_array)
        result = self._landmarker.detect(mp_image)

        num_poses = len(result.pose_landmarks) if result.pose_landmarks else 0
        if num_poses == 0:
            return PoseDetectionResult(
                has_pose=False,
                num_poses_detected=0,
                image_width=width,
                image_height=height,
            )

        # Primary pose landmarks (first detected person)
        primary_landmarks_raw = result.pose_landmarks[0]
        parsed_landmarks: List[LandmarkPoint] = []
        for idx, lm in enumerate(primary_landmarks_raw):
            try:
                name = PoseLandmarkIndex(idx).name
            except ValueError:
                name = f"LANDMARK_{idx}"
            parsed_landmarks.append(
                LandmarkPoint(
                    index=idx,
                    name=name,
                    x=float(lm.x),
                    y=float(lm.y),
                    z=float(lm.z),
                    visibility=float(lm.visibility) if lm.visibility is not None else 1.0,
                    presence=float(lm.presence) if lm.presence is not None else 1.0,
                )
            )

        # World landmarks (in meters)
        parsed_world_landmarks: List[LandmarkPoint] = []
        if result.pose_world_landmarks and len(result.pose_world_landmarks) > 0:
            for idx, lm in enumerate(result.pose_world_landmarks[0]):
                try:
                    name = PoseLandmarkIndex(idx).name
                except ValueError:
                    name = f"LANDMARK_{idx}"
                parsed_world_landmarks.append(
                    LandmarkPoint(
                        index=idx,
                        name=name,
                        x=float(lm.x),
                        y=float(lm.y),
                        z=float(lm.z),
                        visibility=float(lm.visibility) if lm.visibility is not None else 1.0,
                        presence=float(lm.presence) if lm.presence is not None else 1.0,
                    )
                )

        # Segmentation mask
        seg_mask: Optional[np.ndarray] = None
        if result.segmentation_masks and len(result.segmentation_masks) > 0:
            # numpy_view returns float32 probability array (H, W)
            seg_mask = np.array(result.segmentation_masks[0].numpy_view(), copy=True)

        return PoseDetectionResult(
            has_pose=True,
            num_poses_detected=num_poses,
            landmarks=parsed_landmarks,
            world_landmarks=parsed_world_landmarks,
            segmentation_mask=seg_mask,
            image_width=width,
            image_height=height,
        )
