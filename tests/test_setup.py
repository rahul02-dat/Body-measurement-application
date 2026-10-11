"""Smoke test verifying project structure and package setup."""

import csv
from pathlib import Path
import body_measurement


def test_package_metadata():
    """Verify package version is exposed."""
    assert hasattr(body_measurement, "__version__")
    assert body_measurement.__version__ == "0.1.0"


def test_example_schema_exists_and_valid():
    """Verify example CSV schema file exists and has valid required headers."""
    csv_path = Path(__file__).parent.parent / "data" / "measurements.example.csv"
    assert csv_path.exists(), "data/measurements.example.csv must exist"

    required_columns = {
        "participant_id",
        "front_image_path",
        "side_image_path",
        "height_cm",
        "chest_tape_cm",
        "waist_tape_cm",
        "hip_tape_cm",
        "lighting_adequate",
        "posture_upright",
        "feet_visible",
        "clothing_tight",
        "protocol_version",
        "consent_given",
        "retention_agreed",
    }

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(row for row in f if not row.startswith("#"))
        headers = set(reader.fieldnames or [])
        assert required_columns.issubset(headers), (
            f"Missing required columns: {required_columns - headers}"
        )

        rows = list(reader)
        assert len(rows) > 0, "Example CSV must contain at least one example row"
        for row in rows:
            assert row["participant_id"].startswith("SYNTH_")
            height = float(row["height_cm"])
            assert 100.0 <= height <= 230.0
