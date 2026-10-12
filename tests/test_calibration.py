"""Unit tests for Phase S1 calibration experiment and anthropometric analysis."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from body_measurement.calibration import (
    analyze_aspect_ratios,
    evaluate_geometric_ellipse_baseline,
    generate_ansur_calibration_report,
    run_phase_s1_calibration_experiment,
)


@pytest.fixture
def mock_anthropometric_df():
    """Create a mock anthropometric DataFrame matching ANSUR II schema."""
    rng = np.random.default_rng(42)
    n = 100

    heights = rng.uniform(155.0, 190.0, n)
    weights = rng.uniform(50.0, 95.0, n)
    genders = ["Male" if i % 2 == 0 else "Female" for i in range(n)]

    # Generate realistic breadths and depths
    chest_w = rng.uniform(26.0, 36.0, n)
    chest_d = rng.uniform(20.0, 28.0, n)
    waist_w = rng.uniform(24.0, 34.0, n)
    waist_d = rng.uniform(18.0, 26.0, n)

    # Generate approximate true circumferences with slight non-elliptical offset
    from body_measurement.measurement_geometry import calculate_ellipse_circumference
    chest_circs = [calculate_ellipse_circumference(w, d) + float(rng.normal(0.8, 1.2)) for w, d in zip(chest_w, chest_d)]
    waist_circs = [calculate_ellipse_circumference(w, d) + float(rng.normal(0.5, 1.0)) for w, d in zip(waist_w, waist_d)]
    hip_circs = [w * 3.1 + 10.0 for w in waist_w]

    df = pd.DataFrame({
        "subject_id": [f"SUBJ_{i:04d}" for i in range(n)],
        "gender": genders,
        "height_cm": heights,
        "weight_kg": weights,
        "chest_tape_cm": chest_circs,
        "waist_tape_cm": waist_circs,
        "hip_tape_cm": hip_circs,
        "chest_width_cm": chest_w,
        "chest_depth_cm": chest_d,
        "waist_width_cm": waist_w,
        "waist_depth_cm": waist_d,
        "hip_width_cm": [w * 1.05 for w in waist_w],
        "shoulder_width_cm": [h * 0.23 for h in heights],
        "chest_ramanujan_cm": [calculate_ellipse_circumference(w, d) for w, d in zip(chest_w, chest_d)],
        "waist_ramanujan_cm": [calculate_ellipse_circumference(w, d) for w, d in zip(waist_w, waist_d)],
        "chest_aspect_ratio": chest_w / chest_d,
        "waist_aspect_ratio": waist_w / waist_d,
        "bmi": weights / ((heights / 100.0) ** 2),
    })

    def get_cat(b):
        if b < 18.5: return "Underweight"
        if b < 25.0: return "Normal"
        if b < 30.0: return "Overweight"
        return "Obese"

    df["bmi_category"] = df["bmi"].apply(get_cat)
    return df


def test_evaluate_geometric_ellipse_baseline(mock_anthropometric_df):
    """Verify geometric baseline computation returns expected metric fields."""
    res = evaluate_geometric_ellipse_baseline(mock_anthropometric_df)
    assert "chest" in res
    assert "waist" in res

    chest = res["chest"]
    assert chest["sample_count"] == 100
    assert 0.0 < chest["mae"] < 5.0
    assert "signed_bias" in chest
    assert "rmse" in chest
    assert 0.0 <= chest["pct_within_2cm"] <= 100.0


def test_analyze_aspect_ratios(mock_anthropometric_df):
    """Verify aspect ratio analysis computes overall, gender, and BMI breakdowns."""
    ratios = analyze_aspect_ratios(mock_anthropometric_df)
    assert "chest" in ratios
    assert "waist" in ratios

    c_overall = ratios["chest"]["overall"]
    assert c_overall["min"] < c_overall["mean"] < c_overall["max"]
    assert "Male" in ratios["chest"]["by_gender"]
    assert "Female" in ratios["chest"]["by_gender"]


def test_run_phase_s1_calibration_experiment(mock_anthropometric_df):
    """Verify Phase S1 calibration performs train/test split, cross-validation, and held-out evaluation."""
    res = run_phase_s1_calibration_experiment(mock_anthropometric_df, random_seed=42)

    assert res["total_subjects"] == 100
    assert res["train_subjects"] == 80
    assert res["test_subjects"] == 20

    # Verify cross validation across feature sets
    cv = res["cv_results"]["chest"]
    assert "uncalibrated_baseline" in cv
    assert "baseline_only" in cv
    assert "baseline_plus_height" in cv
    assert "baseline_plus_height_weight" in cv

    # Verify held-out test evaluations
    test_eval = res["test_evaluations"]["chest"]
    assert "uncalibrated_overall" in test_eval
    assert "calibrated_overall" in test_eval
    assert "calibrated_male" in test_eval
    assert "calibrated_female" in test_eval

    # Verify model parameters
    models = res["models"]
    assert "chest" in models
    assert "waist" in models
    assert len(models["chest"]["coefficients"]) == 3
    assert len(models["chest"]["scaler_mean"]) == 3


def test_generate_ansur_calibration_report(mock_anthropometric_df, tmp_path):
    """Verify report generation writes markdown with tables and discussion."""
    geom = evaluate_geometric_ellipse_baseline(mock_anthropometric_df)
    ratios = analyze_aspect_ratios(mock_anthropometric_df)
    cal_exp = run_phase_s1_calibration_experiment(mock_anthropometric_df)

    out_file = tmp_path / "test_report.md"
    rep_path = generate_ansur_calibration_report(geom, ratios, cal_exp, out_file)

    assert rep_path.is_file()
    text = rep_path.read_text(encoding="utf-8")
    assert "# Phase S1: Anthropometric Analysis & Calibration Report" in text
    assert "Pure Geometric Baseline Benchmark" in text
    assert "Subgroup Safety Verification" in text
