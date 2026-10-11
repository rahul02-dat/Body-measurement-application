"""Unit tests for participant schemas and manifest loader."""

from pathlib import Path
import pytest
from pydantic import ValidationError

from body_measurement.schemas import (
    ParticipantRecord,
    SchemaValidationError,
    load_participant_manifest,
)


@pytest.fixture
def valid_record_kwargs():
    """Provides a valid dictionary of participant record fields."""
    return {
        "participant_id": "SYNTH_001",
        "front_image_path": "data/raw/synth_001_front.jpg",
        "side_image_path": "data/raw/synth_001_side.jpg",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "chest_tape_cm": 95.0,
        "chest_tape_rep2_cm": 95.6,
        "waist_tape_cm": 80.0,
        "waist_tape_rep2_cm": 80.4,
        "hip_tape_cm": 98.0,
        "hip_tape_rep2_cm": 98.0,
        "shoulder_width_tape_cm": 44.0,
        "inseam_tape_cm": 78.0,
        "lighting_adequate": True,
        "posture_upright": True,
        "feet_visible": True,
        "clothing_tight": True,
        "protocol_version": "v1.0",
        "consent_given": True,
        "retention_agreed": True,
    }


def test_valid_participant_record(valid_record_kwargs):
    """Test valid record instantiation and property calculations."""
    record = ParticipantRecord(**valid_record_kwargs)
    assert record.participant_id == "SYNTH_001"
    assert record.height_cm == 175.0
    # Mean calculation for rep1 and rep2: (95.0 + 95.6) / 2 = 95.3
    assert record.effective_chest_tape_cm == 95.3
    assert record.chest_rep_diff_cm == 0.6
    # Mean for waist: (80.0 + 80.4) / 2 = 80.2
    assert record.effective_waist_tape_cm == 80.2
    assert record.waist_rep_diff_cm == 0.4
    # Equal readings: mean is 98.0, diff is 0.0
    assert record.effective_hip_tape_cm == 98.0
    assert record.hip_rep_diff_cm == 0.0


def test_record_without_repeat_readings(valid_record_kwargs):
    """Test that when rep2 is None, effective value equals reading 1."""
    data = valid_record_kwargs.copy()
    data["chest_tape_rep2_cm"] = None
    data["waist_tape_rep2_cm"] = None
    data["hip_tape_rep2_cm"] = None

    record = ParticipantRecord(**data)
    assert record.effective_chest_tape_cm == 95.0
    assert record.chest_rep_diff_cm is None
    assert record.effective_waist_tape_cm == 80.0
    assert record.effective_hip_tape_cm == 98.0


@pytest.mark.parametrize("invalid_id", [
    "user@example.com",     # email address
    "John Doe",             # personal name with spaces
    "subject/123",          # path-like characters
    "id#123",               # special characters
])
def test_reject_non_anonymized_or_invalid_id(valid_record_kwargs, invalid_id):
    """Ensure participant IDs must be strictly anonymized alphanumeric tokens."""
    data = valid_record_kwargs.copy()
    data["participant_id"] = invalid_id
    with pytest.raises(ValidationError):
        ParticipantRecord(**data)


@pytest.mark.parametrize("invalid_height", [50.0, 99.9, 235.0, -170.0])
def test_reject_out_of_range_height(valid_record_kwargs, invalid_height):
    """Ensure heights outside plausible anthropometric bounds [100, 230] are rejected."""
    data = valid_record_kwargs.copy()
    data["height_cm"] = invalid_height
    with pytest.raises(ValidationError):
        ParticipantRecord(**data)


@pytest.mark.parametrize("field_name", ["chest_tape_cm", "waist_tape_cm", "hip_tape_cm"])
def test_reject_out_of_range_tape_circumference(valid_record_kwargs, field_name):
    """Ensure circumferences outside valid range are rejected."""
    data = valid_record_kwargs.copy()
    data[field_name] = 25.0  # too small
    with pytest.raises(ValidationError):
        ParticipantRecord(**data)

    data[field_name] = 250.0  # too large
    with pytest.raises(ValidationError):
        ParticipantRecord(**data)


def test_reject_missing_required_fields(valid_record_kwargs):
    """Ensure records missing required fields fail validation."""
    for required in ["participant_id", "front_image_path", "side_image_path", "height_cm", "chest_tape_cm", "waist_tape_cm", "hip_tape_cm"]:
        data = valid_record_kwargs.copy()
        data.pop(required)
        with pytest.raises(ValidationError):
            ParticipantRecord(**data)


def test_reject_unconsented_record(valid_record_kwargs):
    """Records without informed consent must fail validation."""
    data = valid_record_kwargs.copy()
    data["consent_given"] = False
    with pytest.raises(ValidationError) as excinfo:
        ParticipantRecord(**data)
    assert "consent_given must be True" in str(excinfo.value)


def test_load_participant_manifest_success():
    """Verify loading the project's example CSV succeeds with verify_images_exist=False."""
    csv_path = Path(__file__).parent.parent / "data" / "measurements.example.csv"
    records = load_participant_manifest(csv_path, verify_images_exist=False)
    assert len(records) == 3
    assert records[0].participant_id == "SYNTH_001"
    assert records[1].participant_id == "SYNTH_002"
    assert records[2].participant_id == "SYNTH_003"


def test_load_participant_manifest_missing_file():
    """Verify loading a nonexistent manifest raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_participant_manifest(Path("nonexistent_manifest.csv"))


def test_load_participant_manifest_verify_images_flag(tmp_path):
    """Verify that verify_images_exist=True catches missing image files."""
    manifest_file = tmp_path / "manifest.csv"
    manifest_file.write_text(
        "participant_id,front_image_path,side_image_path,height_cm,chest_tape_cm,waist_tape_cm,hip_tape_cm,"
        "lighting_adequate,posture_upright,feet_visible,clothing_tight,protocol_version,consent_given,retention_agreed\n"
        "SYNTH_999,missing_front.jpg,missing_side.jpg,170.0,90.0,75.0,95.0,true,true,true,true,v1.0,true,true\n",
        encoding="utf-8",
    )

    # When verification is enabled, missing images raise SchemaValidationError
    with pytest.raises(SchemaValidationError) as excinfo:
        load_participant_manifest(manifest_file, base_dir=tmp_path, verify_images_exist=True)
    assert "Front image file not found" in str(excinfo.value)

    # When verification is disabled, parsing succeeds
    records = load_participant_manifest(manifest_file, base_dir=tmp_path, verify_images_exist=False)
    assert len(records) == 1
    assert records[0].participant_id == "SYNTH_999"


def test_load_participant_manifest_malformed_row(tmp_path):
    """Verify malformed row with invalid units produces structured error."""
    manifest_file = tmp_path / "malformed.csv"
    manifest_file.write_text(
        "participant_id,front_image_path,side_image_path,height_cm,chest_tape_cm,waist_tape_cm,hip_tape_cm,"
        "lighting_adequate,posture_upright,feet_visible,clothing_tight,protocol_version,consent_given,retention_agreed\n"
        "SYNTH_001,front.jpg,side.jpg,NOT_A_NUMBER,90.0,75.0,95.0,true,true,true,true,v1.0,true,true\n",
        encoding="utf-8",
    )

    with pytest.raises(SchemaValidationError) as excinfo:
        load_participant_manifest(manifest_file, verify_images_exist=False)
    assert "Row 2" in str(excinfo.value)
