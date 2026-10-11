"""Configuration parameters and operational thresholds for body measurement."""

from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class ValidationThresholds:
    """Anthropometric and data sanity bounds (in metric units cm and kg)."""

    # Standing height bounds (cm)
    MIN_HEIGHT_CM: float = 100.0
    MAX_HEIGHT_CM: float = 230.0

    # Body weight bounds (kg)
    MIN_WEIGHT_KG: float = 30.0
    MAX_WEIGHT_KG: float = 250.0

    # Circumference bounds (cm)
    MIN_CHEST_TAPE_CM: float = 40.0
    MAX_CHEST_TAPE_CM: float = 200.0

    MIN_WAIST_TAPE_CM: float = 40.0
    MAX_WAIST_TAPE_CM: float = 190.0

    MIN_HIP_TAPE_CM: float = 40.0
    MAX_HIP_TAPE_CM: float = 200.0

    # Exploratory measurements (cm)
    MIN_SHOULDER_WIDTH_CM: float = 25.0
    MAX_SHOULDER_WIDTH_CM: float = 75.0

    MIN_INSEAM_CM: float = 40.0
    MAX_INSEAM_CM: float = 120.0


@dataclass(frozen=True)
class ImageConfig:
    """Image input constraints and limits."""

    SUPPORTED_EXTENSIONS: Set[str] = frozenset({".jpg", ".jpeg", ".png", ".webp"})
    # Safety limit to prevent memory exhaustion / decompression bomb attacks
    MAX_IMAGE_PIXELS: int = 100_000_000  # ~100 megapixels


DEFAULT_THRESHOLDS = ValidationThresholds()
DEFAULT_IMAGE_CONFIG = ImageConfig()
