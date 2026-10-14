"""Unit and integration tests for evaluation metrics, repeat variability, and report generation."""

import json
from pathlib import Path
import pytest

from body_measurement.cli import evaluate_manifest
from body_measurement.evaluation import (
    EvaluationSummary,
    ParticipantPredictionRow,
    calculate_measurement_metrics,
    calculate_repeat_variability,
    evaluate_predictions,
    generate_evaluation_artifacts,
)


def test_calculate_measurement_metrics_exact():
    """Verify statistical metrics calculation on known vector."""
    # errors: [+2.0, -1.0, 0.0]
    y_true = [100.0, 90.0, 80.0]
    y_pred = [102.0, 89.0, 80.0]

    metrics = calculate_measurement_metrics("chest", y_true, y_pred)
    assert metrics.sample_count == 3
    assert metrics.mae == 1.0
    assert metrics.median_ae == 1.0
    assert pytest.approx(metrics.signed_bias, 0.01) == 0.33
    assert pytest.approx(metrics.rmse, 0.01) == 1.29
    assert pytest.approx(metrics.pct_within_1cm, 0.1) == 66.7
    assert metrics.pct_within_2cm == 100.0
    assert metrics.pct_within_3cm == 100.0
    assert metrics.pct_within_5cm == 100.0


def test_calculate_repeat_variability_exact():
    """Verify repeat variability calculations."""
    diffs = [0.2, 0.4, 0.6, 0.0]
    metrics = calculate_repeat_variability("waist", diffs)
    assert metrics.sample_count == 4
    assert metrics.mean_abs_diff == 0.3
    assert metrics.max_abs_diff == 0.6


def test_evaluate_predictions_aggregation():
    """Verify aggregation handles mix of successes and rejections."""
    rows = [
        ParticipantPredictionRow(
            participant_id="P1",
            status="SUCCESS",
            chest_tape_cm=95.0,
            chest_pred_cm=96.0,
            waist_tape_cm=80.0,
            waist_pred_cm=81.0,
            hip_tape_cm=98.0,
            hip_pred_cm=99.0,
            chest_repeat_diff_cm=0.2,
        ),
        ParticipantPredictionRow(
            participant_id="P2",
            status="REJECTED",
            rejection_reasons=["NO_PERSON_DETECTED", "FEET_CROPPED_AT_BOTTOM"],
            chest_tape_cm=90.0,
            waist_tape_cm=75.0,
            hip_tape_cm=92.0,
        ),
    ]

    summary = evaluate_predictions(rows)
    assert summary.total_records == 2
    assert summary.successful_records == 1
    assert summary.rejected_records == 1
    assert summary.rejection_rate == 50.0
    assert summary.rejection_breakdown["NO_PERSON_DETECTED"] == 1
    assert summary.rejection_breakdown["FEET_CROPPED_AT_BOTTOM"] == 1
    assert summary.chest_metrics is not None
    assert summary.chest_metrics.sample_count == 1
    assert summary.chest_metrics.mae == 1.0


def test_generate_evaluation_artifacts(tmp_path):
    """Verify Markdown report, CSV, JSON, and diagnostic plots are generated on disk."""
    rows = [
        ParticipantPredictionRow(
            participant_id=f"P_{i}",
            status="SUCCESS",
            chest_tape_cm=90.0 + i,
            chest_pred_cm=91.0 + i,
            waist_tape_cm=75.0 + i,
            waist_pred_cm=75.5 + i,
            hip_tape_cm=95.0 + i,
            hip_pred_cm=95.2 + i,
            chest_repeat_diff_cm=0.3,
            waist_repeat_diff_cm=0.2,
            hip_repeat_diff_cm=0.4,
        )
        for i in range(5)
    ]

    summary = evaluate_predictions(rows)
    out_dir = tmp_path / "eval_out"
    artifacts = generate_evaluation_artifacts(summary, out_dir)

    assert artifacts["report_md"].is_file()
    assert artifacts["pred_csv"].is_file()
    assert artifacts["metrics_json"].is_file()
    assert len(artifacts["plots"]) == 3
    for p in artifacts["plots"]:
        assert p.is_file()

    # Verify JSON content
    with open(artifacts["metrics_json"], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["total_records"] == 5
        assert data["successful_records"] == 5
        assert data["chest"]["mae"] == 1.0

    # Verify report content
    report_text = artifacts["report_md"].read_text(encoding="utf-8")
    assert "# Feasibility Spike Baseline Evaluation Report" in report_text
    assert "Circumference Accuracy Metrics" in report_text
    assert "Key Limitations & Assumptions Disclosed" in report_text


@pytest.mark.skipif(
    not Path("models/pose_landmarker_full.task").is_file(),
    reason="MediaPipe model binary not downloaded",
)
def test_evaluate_manifest_missing_images_rejection(tmp_path):
    """Verify evaluate_manifest records rejection when referenced images are missing."""
    csv_file = tmp_path / "manifest.csv"
    csv_file.write_text(
        "participant_id,front_image_path,side_image_path,height_cm,chest_tape_cm,waist_tape_cm,hip_tape_cm,"
        "lighting_adequate,posture_upright,feet_visible,clothing_tight,protocol_version,consent_given,retention_agreed\n"
        "TEST_001,absent_f.jpg,absent_s.jpg,175.0,95.0,80.0,98.0,true,true,true,true,v1.0,true,true\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "reports"
    summary, artifacts = evaluate_manifest(
        manifest_csv=csv_file,
        output_dir=out_dir,
        base_dir=tmp_path,
    )

    assert summary.total_records == 1
    assert summary.successful_records == 0
    assert summary.rejected_records == 1
    assert "IMAGE_FILE_NOT_FOUND_ON_DISK" in summary.predictions[0].rejection_reasons
    assert artifacts["report_md"].is_file()
    assert artifacts["pred_csv"].is_file()
