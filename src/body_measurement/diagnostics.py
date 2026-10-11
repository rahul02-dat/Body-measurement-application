"""Diagnostic visual overlays generating side-by-side landmark skeleton and mask composites."""

from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np
from PIL import Image

from body_measurement.image_io import LoadedImage
from body_measurement.pose_detection import POSE_CONNECTIONS, PoseDetectionResult
from body_measurement.quality_checks import PoseQualityReport
from body_measurement.segmentation import extract_binary_mask, extract_bounding_box


def draw_skeleton_on_image(
    rgb_image: np.ndarray,
    detection: PoseDetectionResult,
    line_color: tuple = (0, 215, 255),  # Amber / Cyan in RGB
    point_radius: int = 4,
    line_thickness: int = 2,
) -> np.ndarray:
    """Draw skeleton lines and landmark points on an RGB image copy."""
    annotated = rgb_image.copy()
    h, w = annotated.shape[:2]

    if not detection.has_pose or not detection.landmarks:
        return annotated

    # Draw connection lines
    for start_idx, end_idx in POSE_CONNECTIONS:
        start_lm = detection.get_landmark(start_idx)
        end_lm = detection.get_landmark(end_idx)
        if start_lm is None or end_lm is None:
            continue
        if start_lm.visibility < 0.3 or end_lm.visibility < 0.3:
            continue

        pt1 = (int(start_lm.x * w), int(start_lm.y * h))
        pt2 = (int(end_lm.x * w), int(end_lm.y * h))
        cv2.line(annotated, pt1, pt2, line_color, line_thickness, lineType=cv2.LINE_AA)

    # Draw landmark circles
    for lm in detection.landmarks:
        px = int(lm.x * w)
        py = int(lm.y * h)
        if 0 <= px < w and 0 <= py < h:
            # Green for confident landmarks, red/orange for low visibility
            color = (0, 230, 115) if lm.visibility >= 0.5 else (255, 75, 75)
            cv2.circle(annotated, (px, py), point_radius, color, -1, lineType=cv2.LINE_AA)
            cv2.circle(annotated, (px, py), point_radius + 1, (20, 20, 20), 1, lineType=cv2.LINE_AA)

    return annotated


def draw_segmentation_overlay(
    rgb_image: np.ndarray,
    detection: PoseDetectionResult,
    tint_color: tuple = (40, 180, 250),  # RGB tint
    alpha: float = 0.45,
) -> np.ndarray:
    """Overlay translucent segmentation mask and boundary contour on image copy."""
    annotated = rgb_image.copy()
    h, w = annotated.shape[:2]

    if detection.segmentation_mask is None:
        cv2.putText(
            annotated,
            "NO MASK AVAILABLE",
            (20, h // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 60, 60),
            2,
            cv2.LINE_AA,
        )
        return annotated

    # Convert probability mask to binary uint8
    binary = extract_binary_mask(detection.segmentation_mask, threshold=0.5)

    # Resize mask if dimensions differ from image
    if binary.shape[:2] != (h, w):
        binary = cv2.resize(binary, (w, h), interpolation=cv2.INTER_NEAREST)

    # Colorize foreground
    color_mask = np.zeros_like(annotated)
    color_mask[binary > 0] = tint_color

    # Blend
    cv2.addWeighted(color_mask, alpha, annotated, 1.0, 0, annotated)

    # Draw silhouette contour boundary
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(annotated, contours, -1, (255, 255, 255), 2, lineType=cv2.LINE_AA)

    # Draw bounding box
    bbox = extract_bounding_box(binary)
    if bbox:
        ymin, xmin, ymax, xmax = bbox
        cv2.rectangle(annotated, (xmin, ymin), (xmax, ymax), (255, 220, 0), 1, lineType=cv2.LINE_AA)

    return annotated


def create_diagnostic_overlay(
    image: Union[LoadedImage, np.ndarray],
    detection: PoseDetectionResult,
    quality_report: Optional[PoseQualityReport] = None,
    output_path: Optional[Union[str, Path]] = None,
    title: str = "Pose & Silhouette Diagnostic",
) -> np.ndarray:
    """
    Generate side-by-side composite:
    - Left: Original RGB with landmark skeleton overlay.
    - Right: Person segmentation mask contour and bounding box.
    - Top banner: Quality validation status and metrics.

    Args:
        image: LoadedImage or RGB numpy array.
        detection: PoseDetectionResult.
        quality_report: Optional PoseQualityReport.
        output_path: Optional file path to save the composite image.
        title: Title to display in top banner.

    Returns:
        RGB numpy array of composite diagnostic image.
    """
    if isinstance(image, LoadedImage):
        rgb_array = image.rgb_array
    elif isinstance(image, np.ndarray):
        rgb_array = image
    else:
        raise TypeError(f"Expected LoadedImage or np.ndarray, got {type(image)}")

    h, w = rgb_array.shape[:2]

    # Render left and right panels
    left_panel = draw_skeleton_on_image(rgb_array, detection)
    right_panel = draw_segmentation_overlay(rgb_array, detection)

    # Side-by-side concatenation
    panels = np.hstack([left_panel, right_panel])

    # Add header banner
    banner_height = 60
    total_width = w * 2
    banner = np.full((banner_height, total_width, 3), 32, dtype=np.uint8)

    # Panel captions
    cv2.putText(banner, f"{title} | Left: Landmarks Skeleton", (20, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1, cv2.LINE_AA)
    cv2.putText(banner, "Right: Silhouette Segmentation", (w + 20, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1, cv2.LINE_AA)

    # Quality status badge
    if quality_report is not None:
        if quality_report.is_valid:
            status_text = f"VALID (Mean Vis: {quality_report.mean_landmark_visibility:.2f})"
            status_color = (46, 204, 113)  # Emerald green
        else:
            reasons_str = ", ".join(quality_report.rejection_reasons)
            status_text = f"REJECTED: {reasons_str}"
            status_color = (231, 76, 60)   # Red
        cv2.putText(banner, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 1, cv2.LINE_AA)

    composite = np.vstack([banner, panels])

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        pil_img = Image.fromarray(composite)
        pil_img.save(out)

    return composite
