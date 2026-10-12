"""Unit and integration tests for Phase S0-H synthetic feasibility demo."""

import json
from pathlib import Path
import pytest

from body_measurement.synthetic_demo import (
    generate_synthetic_pilot_cohort,
    render_synthetic_mannequin_image,
    run_synthetic_feasibility_pipeline,
)


def test_generate_synthetic_pilot_cohort():
    """Verify synthetic pilot cohort contains N=25 participants with valid values and edge cases."""
    cohort = generate_synthetic_pilot_cohort(n_participants=25, random_seed=42)
    assert len(cohort) == 25

    # Check participant structure
    first = cohort[0]
    assert first["participant_id"] == "SYNTH_PILOT_001"
    assert 150.0 <= first["height_cm"] <= 200.0
    assert 70.0 <= first["chest_tape_cm"] <= 130.0
    assert 55.0 <= first["waist_tape_cm"] <= 120.0
    assert 75.0 <= first["hip_tape_cm"] <= 130.0
    assert abs(first["chest_tape_cm"] - first["chest_tape_rep2_cm"]) < 2.0

    # Verify edge cases are present
    slouch_cases = [c for c in cohort if c["is_slouch_edge_case"]]
    crop_cases = [c for c in cohort if c["is_crop_edge_case"]]
    assert len(slouch_cases) == 1
    assert len(crop_cases) == 1
    assert slouch_cases[0]["tilt_degrees"] > 8.0


def test_render_synthetic_mannequin_image():
    """Verify mannequin renderer produces correct dimensions and levels."""
    img, levels = render_synthetic_mannequin_image(
        height_px=800,
        width_px=400,
        view="front",
        chest_dim_cm=30.0,
        waist_dim_cm=24.0,
        hip_dim_cm=32.0,
        pixels_per_cm=4.0,
    )
    assert img.shape == (800, 400, 3)
    assert "chest" in levels
    assert "waist" in levels
    assert "hip" in levels
    assert levels["chest"] < levels["waist"] < levels["hip"]


def test_run_synthetic_feasibility_pipeline(tmp_path):
    """Verify synthetic feasibility pipeline generates all artifacts and validates against targets."""
    out_dir = tmp_path / "feasibility_test_out"
    summary, artifacts = run_synthetic_feasibility_pipeline(
        output_dir=out_dir,
        n_participants=25,
        random_seed=42,
    )

    # Verify summary numbers
    assert summary.total_records == 25
    assert summary.successful_records == 23
    assert summary.rejected_records == 2
    assert summary.rejection_rate == 8.0

    # Verify fail-safe rejection codes
    assert "TORSO_SLOUCH_OR_TILT_EXCESSIVE (9.4° > 8.0°)" in summary.rejection_breakdown
    assert "FEET_CROPPED_AT_BOTTOM" in summary.rejection_breakdown

    # Verify circumference error metrics
    assert summary.chest_metrics is not None
    assert summary.chest_metrics.mae <= 2.0
    assert summary.waist_metrics is not None
    assert summary.waist_metrics.mae <= 2.0
    assert summary.hip_metrics is not None
    assert summary.hip_metrics.mae <= 2.0

    # Verify sizing recommendation metrics
    assert summary.sizing_result is not None
    assert summary.sizing_result.evaluated_count == 23
    assert summary.sizing_result.exact_accuracy_pct >= 60.0
    assert summary.sizing_result.adjacent_accuracy_pct >= 90.0

    # Verify generated artifact files exist
    assert artifacts["feasibility_report"].is_file()
    assert artifacts["report_md"].is_file()
    assert artifacts["pred_csv"].is_file()
    assert artifacts["metrics_json"].is_file()
    assert len(artifacts["plots"]) == 3
    for plot_path in artifacts["plots"]:
        assert plot_path.is_file()

    # Verify Feasibility Gate Report contents
    report_text = artifacts["feasibility_report"].read_text(encoding="utf-8")
    assert "# Phase S0-H: Feasibility Gate Evaluation Report" in report_text
    assert "Provisional Criteria Assessment" in report_text
    assert "Option A: Proceed to a Larger Validation Study" in report_text
    assert "Option B: Revise the Capture or Geometry Pipeline" in report_text
    assert "Option C: Stop or Change Use Case" in report_text
