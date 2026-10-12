"""Unit tests for batch execution and CLI operations."""

from pathlib import Path
from PIL import Image
import pytest

from body_measurement.cli import process_image_view, process_participant_record, run_batch_manifest
from body_measurement.pose_detection import PoseDetector
from body_measurement.schemas import ParticipantRecord


@pytest.fixture
def synthetic_pair(tmp_path):
    """Creates a temporary image pair and manifest for batch pipeline testing."""
    img_dir = tmp_path / "images"
    img_dir.mkdir()

    front_img = Image.new("RGB", (200, 400), color=(100, 100, 100))
    side_img = Image.new("RGB", (200, 400), color=(120, 120, 120))

    front_path = img_dir / "test_front.jpg"
    side_path = img_dir / "test_side.jpg"

    front_img.save(front_path)
    side_img.save(side_path)

    manifest_path = tmp_path / "test_manifest.csv"
    manifest_path.write_text(
        "participant_id,front_image_path,side_image_path,height_cm,chest_tape_cm,waist_tape_cm,hip_tape_cm,"
        "lighting_adequate,posture_upright,feet_visible,clothing_tight,protocol_version,consent_given,retention_agreed\n"
        f"TEST_001,images/test_front.jpg,images/test_side.jpg,175.0,95.0,80.0,98.0,true,true,true,true,v1.0,true,true\n",
        encoding="utf-8",
    )

    return {
        "front": front_path,
        "side": side_path,
        "manifest": manifest_path,
        "base_dir": tmp_path,
    }


def test_process_image_view(synthetic_pair, tmp_path):
    """Verify single view processing produces structured dict and overlay image."""
    model_path = Path(__file__).parent.parent / "models" / "pose_landmarker_full.task"
    if not model_path.is_file():
        pytest.skip("Model binary not found")

    out_dir = tmp_path / "out"
    with PoseDetector(model_asset_path=model_path) as detector:
        res = process_image_view(
            image_path=synthetic_pair["front"],
            view_name="front",
            detector=detector,
            output_dir=out_dir,
            participant_id="TEST_001",
        )

        assert res["view"] == "front"
        assert "has_pose" in res
        assert "is_valid" in res
        assert "rejection_reasons" in res
        assert res["diagnostic_overlay_path"] is not None
        assert Path(res["diagnostic_overlay_path"]).is_file()


def test_process_participant_record(synthetic_pair, tmp_path):
    """Verify processing participant record runs both views."""
    model_path = Path(__file__).parent.parent / "models" / "pose_landmarker_full.task"
    if not model_path.is_file():
        pytest.skip("Model binary not found")

    record = ParticipantRecord(
        participant_id="TEST_P1",
        front_image_path="images/test_front.jpg",
        side_image_path="images/test_side.jpg",
        height_cm=170.0,
        chest_tape_cm=90.0,
        waist_tape_cm=75.0,
        hip_tape_cm=95.0,
        lighting_adequate=True,
        posture_upright=True,
        feet_visible=True,
        clothing_tight=True,
        protocol_version="v1.0",
        consent_given=True,
        retention_agreed=True,
    )

    out_dir = tmp_path / "out"
    with PoseDetector(model_asset_path=model_path) as detector:
        summary = process_participant_record(
            record=record,
            detector=detector,
            base_dir=synthetic_pair["base_dir"],
            output_dir=out_dir,
        )

        assert summary["participant_id"] == "TEST_P1"
        assert "front" in summary
        assert "side" in summary
        assert "overall_valid" in summary


def test_run_batch_manifest(synthetic_pair, tmp_path):
    """Verify run_batch_manifest processes manifest and exports JSON summary."""
    model_path = Path(__file__).parent.parent / "models" / "pose_landmarker_full.task"
    if not model_path.is_file():
        pytest.skip("Model binary not found")

    out_dir = tmp_path / "batch_out"
    results = run_batch_manifest(
        manifest_csv=synthetic_pair["manifest"],
        output_dir=out_dir,
        base_dir=synthetic_pair["base_dir"],
        model_path=model_path,
    )

    assert len(results) == 1
    assert (out_dir / "pose_batch_summary.json").is_file()


def test_cli_run_synthetic_demo(tmp_path, monkeypatch):
    """Verify CLI main() dispatches --run-synthetic-demo and produces reports."""
    from body_measurement.cli import main
    import sys

    out_dir = tmp_path / "cli_demo_out"
    monkeypatch.setattr(
        sys,
        "argv",
        ["body-measurement", "--run-synthetic-demo", "--output-dir", str(out_dir)],
    )

    main()

    assert (out_dir / "FEASIBILITY_GATE_REPORT.md").is_file()
    assert (out_dir / "per_participant_predictions.csv").is_file()
    assert (out_dir / "metrics_summary.json").is_file()


def test_validate_manifest_command_valid(synthetic_pair):
    """Verify validate_manifest_command returns True when manifest and images are valid."""
    from body_measurement.cli import validate_manifest_command

    result = validate_manifest_command(
        manifest_csv=synthetic_pair["manifest"],
        base_dir=synthetic_pair["base_dir"],
    )
    assert result is True


def test_validate_manifest_command_missing_images(tmp_path):
    """Verify validate_manifest_command returns False when referenced image files do not exist."""
    from body_measurement.cli import validate_manifest_command

    csv_file = tmp_path / "broken_manifest.csv"
    csv_file.write_text(
        "participant_id,front_image_path,side_image_path,height_cm,chest_tape_cm,waist_tape_cm,hip_tape_cm,"
        "lighting_adequate,posture_upright,feet_visible,clothing_tight,protocol_version,consent_given,retention_agreed\n"
        "TEST_999,nonexistent_f.jpg,nonexistent_s.jpg,175.0,95.0,80.0,98.0,true,true,true,true,v1.0,true,true\n",
        encoding="utf-8",
    )

    result = validate_manifest_command(csv_file, base_dir=tmp_path)
    assert result is False


def test_cli_validate_manifest_flag(synthetic_pair, monkeypatch):
    """Verify CLI main() dispatches --validate-manifest and exits 0 on valid manifest."""
    from body_measurement.cli import main
    import sys

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "body-measurement",
            "--validate-manifest",
            str(synthetic_pair["manifest"]),
            "--base-dir",
            str(synthetic_pair["base_dir"]),
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
