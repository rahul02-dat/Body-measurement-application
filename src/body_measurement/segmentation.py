"""Segmentation mask post-processing and geometric extraction functions."""

from typing import Optional, Tuple
import cv2
import numpy as np


def extract_binary_mask(mask_probability: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """
    Convert a floating-point probability segmentation mask to a binary uint8 mask (0 or 255).

    Args:
        mask_probability: 2D numpy array with float values in [0.0, 1.0].
        threshold: Decision threshold for foreground classification.

    Returns:
        Binary uint8 mask of same shape where foreground is 255 and background is 0.
    """
    if mask_probability.ndim != 2:
        raise ValueError(f"Expected 2D mask array, got shape {mask_probability.shape}")

    binary = (mask_probability >= threshold).astype(np.uint8) * 255
    return binary


def extract_bounding_box(binary_mask: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """
    Compute tight bounding box enclosing foreground pixels (ymin, xmin, ymax, xmax).

    Returns:
        Tuple of (ymin, xmin, ymax, xmax) or None if no foreground pixels exist.
    """
    if binary_mask.ndim != 2:
        raise ValueError(f"Expected 2D binary mask array, got shape {binary_mask.shape}")

    y_indices, x_indices = np.where(binary_mask > 0)
    if len(y_indices) == 0:
        return None

    ymin = int(np.min(y_indices))
    ymax = int(np.max(y_indices))
    xmin = int(np.min(x_indices))
    xmax = int(np.max(x_indices))

    return ymin, xmin, ymax, xmax


def extract_mask_width_at_y(binary_mask: np.ndarray, y: int) -> int:
    """
    Compute foreground pixel width span (xmax - xmin + 1) at horizontal row y.

    Returns:
        Integer pixel width, or 0 if row contains no foreground pixels.
    """
    if y < 0 or y >= binary_mask.shape[0]:
        return 0

    row = binary_mask[y, :]
    x_indices = np.where(row > 0)[0]
    if len(x_indices) == 0:
        return 0

    return int(x_indices[-1] - x_indices[0] + 1)


def calculate_mask_coverage(binary_mask: np.ndarray) -> float:
    """Calculate the ratio of foreground pixels to total image pixels."""
    total_pixels = binary_mask.size
    if total_pixels == 0:
        return 0.0
    fg_pixels = np.count_nonzero(binary_mask > 0)
    return float(fg_pixels / total_pixels)


def keep_largest_component(binary_mask: np.ndarray) -> np.ndarray:
    """
    Retain only the largest connected component (the primary person silhouette)
    and suppress disconnected background artifacts.
    """
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
    if num_labels <= 1:
        return binary_mask

    # Background is label 0; find label with maximum area among foreground (labels >= 1)
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest_label = int(np.argmax(areas) + 1)

    cleaned = np.zeros_like(binary_mask)
    cleaned[labels == largest_label] = 255
    return cleaned
