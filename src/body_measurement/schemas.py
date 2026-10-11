"""Validated data structures and schema definitions for participant measurements."""

import csv
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from body_measurement.config import DEFAULT_THRESHOLDS, ValidationThresholds


class SchemaValidationError(ValueError):
    """Raised when participant data or CSV rows fail schema validation."""

    def __init__(self, message: str, row_index: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.row_index = row_index
        self.details = details or {}


class ParticipantRecord(BaseModel):
    """Validated participant record containing measurements, flags, and image paths."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    participant_id: str = Field(
        ...,
        description="Randomized, non-identifying participant ID (e.g. P001, SYNTH_001).",
    )
    front_image_path: str = Field(..., min_length=1, description="Path to front-view photo.")
    side_image_path: str = Field(..., min_length=1, description="Path to side-view photo.")

    height_cm: float = Field(
        ...,
        ge=DEFAULT_THRESHOLDS.MIN_HEIGHT_CM,
        le=DEFAULT_THRESHOLDS.MAX_HEIGHT_CM,
        description="User-reported standing height in cm (primary scale anchor).",
    )
    weight_kg: Optional[float] = Field(
        None,
        ge=DEFAULT_THRESHOLDS.MIN_WEIGHT_KG,
        le=DEFAULT_THRESHOLDS.MAX_WEIGHT_KG,
        description="Optional body weight in kg.",
    )

    chest_tape_cm: float = Field(
        ...,
        ge=DEFAULT_THRESHOLDS.MIN_CHEST_TAPE_CM,
        le=DEFAULT_THRESHOLDS.MAX_CHEST_TAPE_CM,
        description="Ground truth chest/bust circumference (Reading 1) in cm.",
    )
    chest_tape_rep2_cm: Optional[float] = Field(
        None,
        ge=DEFAULT_THRESHOLDS.MIN_CHEST_TAPE_CM,
        le=DEFAULT_THRESHOLDS.MAX_CHEST_TAPE_CM,
        description="Optional repeat reading for chest circumference in cm.",
    )

    waist_tape_cm: float = Field(
        ...,
        ge=DEFAULT_THRESHOLDS.MIN_WAIST_TAPE_CM,
        le=DEFAULT_THRESHOLDS.MAX_WAIST_TAPE_CM,
        description="Ground truth waist circumference (Reading 1) in cm.",
    )
    waist_tape_rep2_cm: Optional[float] = Field(
        None,
        ge=DEFAULT_THRESHOLDS.MIN_WAIST_TAPE_CM,
        le=DEFAULT_THRESHOLDS.MAX_WAIST_TAPE_CM,
        description="Optional repeat reading for waist circumference in cm.",
    )

    hip_tape_cm: float = Field(
        ...,
        ge=DEFAULT_THRESHOLDS.MIN_HIP_TAPE_CM,
        le=DEFAULT_THRESHOLDS.MAX_HIP_TAPE_CM,
        description="Ground truth hip circumference (Reading 1) in cm.",
    )
    hip_tape_rep2_cm: Optional[float] = Field(
        None,
        ge=DEFAULT_THRESHOLDS.MIN_HIP_TAPE_CM,
        le=DEFAULT_THRESHOLDS.MAX_HIP_TAPE_CM,
        description="Optional repeat reading for hip circumference in cm.",
    )

    shoulder_width_tape_cm: Optional[float] = Field(
        None,
        ge=DEFAULT_THRESHOLDS.MIN_SHOULDER_WIDTH_CM,
        le=DEFAULT_THRESHOLDS.MAX_SHOULDER_WIDTH_CM,
        description="Exploratory biacromial shoulder width in cm.",
    )
    inseam_tape_cm: Optional[float] = Field(
        None,
        ge=DEFAULT_THRESHOLDS.MIN_INSEAM_CM,
        le=DEFAULT_THRESHOLDS.MAX_INSEAM_CM,
        description="Exploratory inseam length in cm.",
    )

    # Capture-quality flags
    lighting_adequate: bool = Field(..., description="Lighting is even and shadow-free.")
    posture_upright: bool = Field(..., description="Subject stood upright with level posture.")
    feet_visible: bool = Field(..., description="Both feet and ground contact visible.")
    clothing_tight: bool = Field(..., description="Subject wore tight-fitting clothing.")

    # Protocol & Governance
    protocol_version: str = Field(..., min_length=1, description="Protocol version string.")
    consent_given: bool = Field(..., description="Explicit informed consent documented.")
    retention_agreed: bool = Field(..., description="Agreement to pilot retention policy.")

    @field_validator("participant_id")
    @classmethod
    def validate_anonymized_id(cls, value: str) -> str:
        """Enforce strict non-identifying participant ID pattern to safeguard privacy."""
        # Must not contain email addresses, URLs, or personal name spaces
        if "@" in value or " " in value or "/" in value or "\\" in value:
            raise ValueError(
                f"Participant ID '{value}' contains invalid characters. "
                "Must be a pseudonymous identifier without spaces or email addresses."
            )
        # Expected standard pattern e.g. P001, PARTICIPANT_001, SYNTH_001
        pattern = r"^[A-Za-z0-9_\-]+$"
        if not re.match(pattern, value):
            raise ValueError(f"Participant ID '{value}' contains invalid special characters.")
        return value

    @field_validator("consent_given")
    @classmethod
    def validate_consent(cls, value: bool) -> bool:
        """Participant records cannot be processed without documented consent."""
        if not value:
            raise ValueError("Cannot process record: consent_given must be True.")
        return value

    @property
    def effective_chest_tape_cm(self) -> float:
        """Consolidated chest ground truth: mean of readings if rep2 is present, else rep1."""
        if self.chest_tape_rep2_cm is not None:
            return round((self.chest_tape_cm + self.chest_tape_rep2_cm) / 2.0, 2)
        return self.chest_tape_cm

    @property
    def effective_waist_tape_cm(self) -> float:
        """Consolidated waist ground truth: mean of readings if rep2 is present, else rep1."""
        if self.waist_tape_rep2_cm is not None:
            return round((self.waist_tape_cm + self.waist_tape_rep2_cm) / 2.0, 2)
        return self.waist_tape_cm

    @property
    def effective_hip_tape_cm(self) -> float:
        """Consolidated hip ground truth: mean of readings if rep2 is present, else rep1."""
        if self.hip_tape_rep2_cm is not None:
            return round((self.hip_tape_cm + self.hip_tape_rep2_cm) / 2.0, 2)
        return self.hip_tape_cm

    @property
    def chest_rep_diff_cm(self) -> Optional[float]:
        """Absolute difference between repeat chest tape readings."""
        if self.chest_tape_rep2_cm is not None:
            return round(abs(self.chest_tape_cm - self.chest_tape_rep2_cm), 2)
        return None

    @property
    def waist_rep_diff_cm(self) -> Optional[float]:
        """Absolute difference between repeat waist tape readings."""
        if self.waist_tape_rep2_cm is not None:
            return round(abs(self.waist_tape_cm - self.waist_tape_rep2_cm), 2)
        return None

    @property
    def hip_rep_diff_cm(self) -> Optional[float]:
        """Absolute difference between repeat hip tape readings."""
        if self.hip_tape_rep2_cm is not None:
            return round(abs(self.hip_tape_cm - self.hip_tape_rep2_cm), 2)
        return None

    def validate_images_exist(self, base_dir: Optional[Union[str, Path]] = None) -> None:
        """Verify that front and side image files exist on the local filesystem."""
        root = Path(base_dir) if base_dir else Path.cwd()
        front_path = root / self.front_image_path
        side_path = root / self.side_image_path

        if not front_path.is_file():
            raise FileNotFoundError(
                f"Front image file not found for participant '{self.participant_id}': {front_path}"
            )
        if not side_path.is_file():
            raise FileNotFoundError(
                f"Side image file not found for participant '{self.participant_id}': {side_path}"
            )


def _parse_bool(val: Any) -> bool:
    """Parse flexible boolean strings from CSV."""
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in {"true", "1", "yes", "y"}:
        return True
    if s in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"Cannot parse '{val}' as boolean.")


def _clean_csv_row(raw_row: Dict[str, str]) -> Dict[str, Any]:
    """Clean empty strings and convert types for Pydantic parsing."""
    cleaned: Dict[str, Any] = {}
    for k, v in raw_row.items():
        if k is None:
            continue
        key = k.strip()
        val = v.strip() if isinstance(v, str) else v
        if val == "" or val is None:
            cleaned[key] = None
        elif key in {"lighting_adequate", "posture_upright", "feet_visible", "clothing_tight", "consent_given", "retention_agreed"}:
            cleaned[key] = _parse_bool(val)
        else:
            cleaned[key] = val
    return cleaned


def load_participant_manifest(
    csv_path: Union[str, Path],
    base_dir: Optional[Union[str, Path]] = None,
    verify_images_exist: bool = False,
) -> List[ParticipantRecord]:
    """
    Safely load and validate a CSV participant manifest.

    Args:
        csv_path: Path to the CSV file.
        base_dir: Optional root directory to resolve relative image paths against.
        verify_images_exist: If True, checks that image files exist on disk.

    Returns:
        List of validated ParticipantRecord objects.

    Raises:
        SchemaValidationError: If any row is malformed or fails schema constraints.
        FileNotFoundError: If the CSV file does not exist.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Manifest CSV not found: {path}")

    records: List[ParticipantRecord] = []
    errors: List[str] = []

    with open(path, mode="r", encoding="utf-8-sig") as f:
        # Filter comments and empty lines
        lines = (line for line in f if line.strip() and not line.strip().startswith("#"))
        reader = csv.DictReader(lines)

        if reader.fieldnames is None:
            raise SchemaValidationError(f"CSV file '{path}' has no header row.")

        for row_idx, raw_row in enumerate(reader, start=2):
            try:
                cleaned = _clean_csv_row(raw_row)
                record = ParticipantRecord.model_validate(cleaned)
                if verify_images_exist:
                    record.validate_images_exist(base_dir=base_dir)
                records.append(record)
            except Exception as e:
                errors.append(f"Row {row_idx}: {e}")

    if errors:
        error_summary = "\n".join(errors)
        raise SchemaValidationError(
            f"Failed to load manifest '{path}' due to {len(errors)} validation errors:\n{error_summary}",
            details={"error_count": len(errors), "errors": errors},
        )

    return records
