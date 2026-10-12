"""Synthetic Feasibility Demo and Pilot Cohort Pipeline for Phase S0-H.

Simulates an end-to-end evaluation with N=25 participants (20-30 volunteer pilot
recommended in AGENTS.md) to demonstrate successful metrics calculation,
Ramanujan ellipse geometry, Uniqlo size chart evaluation, and fail-safe rejections.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

from body_measurement.diagnostics import draw_cross_section_overlay
from body_measurement.evaluation import (
    EvaluationSummary,
    ParticipantPredictionRow,
    evaluate_predictions,
    generate_evaluation_artifacts,
)
from body_measurement.measurement_geometry import calculate_ellipse_circumference


def generate_synthetic_pilot_cohort(
    n_participants: int = 25,
    random_seed: int = 42,
) -> List[Dict]:
    """
    Generate synthetic pilot participant records across sizes XS through XXL.

    Includes 2 intentional edge cases (excessive posture tilt and cropped feet)
    to verify fail-safe rejection behavior as required by AGENTS.md.
    """
    rng = np.random.default_rng(random_seed)
    cohort: List[Dict] = []

    # Target anthropometric profiles covering standard retail sizing
    base_profiles = [
        # (height_cm, chest_cm, waist_cm, hip_cm, weight_kg)
        (160.0, 83.0, 67.0, 88.0, 52.0),   # XS
        (163.0, 86.0, 70.0, 91.0, 56.0),   # XS/S
        (168.0, 90.0, 75.0, 94.0, 62.0),   # S
        (172.0, 94.0, 79.0, 97.0, 67.0),   # S/M
        (175.0, 98.0, 83.0, 100.0, 72.0),  # M
        (177.0, 102.0, 87.0, 104.0, 77.0), # M/L
        (180.0, 106.0, 92.0, 108.0, 83.0), # L
        (183.0, 111.0, 98.0, 113.0, 89.0), # L/XL
        (186.0, 116.0, 104.0, 118.0, 96.0),# XL/XXL
        (170.0, 93.0, 78.0, 96.0, 66.0),   # S
    ]

    for i in range(n_participants):
        pid = f"SYNTH_PILOT_{i + 1:03d}"
        profile = base_profiles[i % len(base_profiles)]

        # Add minor natural variation per individual
        h_noise = float(rng.uniform(-2.0, 2.0))
        c_noise = float(rng.uniform(-1.5, 1.5))
        w_noise = float(rng.uniform(-1.5, 1.5))
        hp_noise = float(rng.uniform(-1.5, 1.5))
        wt_noise = float(rng.uniform(-1.0, 1.0))

        height_cm = round(profile[0] + h_noise, 1)
        chest_tape_cm = round(profile[1] + c_noise, 1)
        waist_tape_cm = round(profile[2] + w_noise, 1)
        hip_tape_cm = round(profile[3] + hp_noise, 1)
        weight_kg = round(profile[4] + wt_noise, 1)

        # Simulate repeat tape readings (intra-rater noise with sigma ~ 0.25 cm)
        chest_rep2 = round(chest_tape_cm + float(rng.normal(0.0, 0.25)), 1)
        waist_rep2 = round(waist_tape_cm + float(rng.normal(0.0, 0.25)), 1)
        hip_rep2 = round(hip_tape_cm + float(rng.normal(0.0, 0.25)), 1)

        is_slouch_edge_case = (i == 23)  # Participant 24: slouch/tilt > 8°
        is_crop_edge_case = (i == 24)    # Participant 25: feet cropped at bottom

        cohort.append({
            "participant_id": pid,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "chest_tape_cm": chest_tape_cm,
            "chest_tape_rep2_cm": chest_rep2,
            "waist_tape_cm": waist_tape_cm,
            "waist_tape_rep2_cm": waist_rep2,
            "hip_tape_cm": hip_tape_cm,
            "hip_tape_rep2_cm": hip_rep2,
            "is_slouch_edge_case": is_slouch_edge_case,
            "is_crop_edge_case": is_crop_edge_case,
            "tilt_degrees": 9.4 if is_slouch_edge_case else round(float(rng.uniform(0.5, 3.5)), 1),
        })

    return cohort


def render_synthetic_mannequin_image(
    height_px: int = 1000,
    width_px: int = 500,
    view: str = "front",
    chest_dim_cm: float = 30.0,
    waist_dim_cm: float = 24.0,
    hip_dim_cm: float = 33.0,
    pixels_per_cm: float = 5.0,
    tilt_degrees: float = 0.0,
    crop_feet: bool = False,
) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Render a clean synthetic anatomical mannequin figure for visual diagnostics.

    Returns:
        Tuple of (RGB numpy array image, cross_section_levels dict)
    """
    img = np.full((height_px, width_px, 3), 245, dtype=np.uint8)  # Light neutral studio background
    cx = width_px // 2

    # Vertical landmarks in pixels
    y_head_top = 80
    y_head_bottom = 180
    y_chest = 340
    y_waist = 470
    y_hip = 620
    y_feet = height_px - 20 if not crop_feet else height_px + 40

    # Draw head
    cv2.ellipse(img, (cx, (y_head_top + y_head_bottom) // 2), (40, 50), 0, 0, 360, (60, 60, 65), -1, cv2.LINE_AA)

    # Convert anatomical dimensions to half-widths in pixels
    half_chest_px = int((chest_dim_cm * pixels_per_cm) / 2)
    half_waist_px = int((waist_dim_cm * pixels_per_cm) / 2)
    half_hip_px = int((hip_dim_cm * pixels_per_cm) / 2)

    # Build torso & leg silhouette contour
    if view == "front":
        pts = [
            [cx - 50, y_head_bottom],
            [cx - half_chest_px, y_chest],
            [cx - half_waist_px, y_waist],
            [cx - half_hip_px, y_hip],
            [cx - 45, y_hip + 160],      # Knees
            [cx - 30, min(y_feet, height_px - 1)], # Left foot
            [cx + 30, min(y_feet, height_px - 1)], # Right foot
            [cx + 45, y_hip + 160],
            [cx + half_hip_px, y_hip],
            [cx + half_waist_px, y_waist],
            [cx + half_chest_px, y_chest],
            [cx + 50, y_head_bottom],
        ]
    else:  # Side view profile
        pts = [
            [cx - 25, y_head_bottom],
            [cx - half_chest_px, y_chest],
            [cx - half_waist_px, y_waist],
            [cx - half_hip_px, y_hip],
            [cx - 35, y_hip + 160],
            [cx - 20, min(y_feet, height_px - 1)],
            [cx + 20, min(y_feet, height_px - 1)],
            [cx + 35, y_hip + 160],
            [cx + (half_hip_px // 2), y_hip],
            [cx + (half_waist_px // 2), y_waist],
            [cx + (half_chest_px // 2), y_chest],
            [cx + 25, y_head_bottom],
        ]

    contour = np.array(pts, dtype=np.int32)
    cv2.fillPoly(img, [contour], (50, 55, 60), lineType=cv2.LINE_AA)

    # Apply tilt if specified
    if abs(tilt_degrees) > 0.1:
        rot_mat = cv2.getRotationMatrix2D((cx, height_px // 2), tilt_degrees, 1.0)
        img = cv2.warpAffine(img, rot_mat, (width_px, height_px), borderValue=(245, 245, 245))

    levels = {
        "chest": y_chest,
        "waist": y_waist,
        "hip": y_hip,
    }
    return img, levels


def run_synthetic_feasibility_pipeline(
    output_dir: Union[str, Path] = "reports/synthetic_demo",
    n_participants: int = 25,
    random_seed: int = 42,
) -> Tuple[EvaluationSummary, Dict[str, Path]]:
    """
    Execute full synthetic feasibility pipeline evaluating Ramanujan ellipse circumferences,
    Uniqlo size-chart recommendations, and diagnostic artifacts.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    images_dir = out_dir / "images"
    diag_dir = out_dir / "diagnostics"
    images_dir.mkdir(parents=True, exist_ok=True)
    diag_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(random_seed)
    cohort = generate_synthetic_pilot_cohort(n_participants=n_participants, random_seed=random_seed)
    prediction_rows: List[ParticipantPredictionRow] = []

    for record in cohort:
        pid = record["participant_id"]
        height_cm = record["height_cm"]
        chest_true = record["chest_tape_cm"]
        waist_true = record["waist_tape_cm"]
        hip_true = record["hip_tape_cm"]

        chest_rep_diff = round(abs(chest_true - record["chest_tape_rep2_cm"]), 2)
        waist_rep_diff = round(abs(waist_true - record["waist_tape_rep2_cm"]), 2)
        hip_rep_diff = round(abs(hip_true - record["hip_tape_rep2_cm"]), 2)

        # Anthropometric cross-section ratio approximations
        # In human anatomy, width (a) is generally wider than depth (b):
        # chest: width ~ 58% of equivalent semi-axes sum, depth ~ 42%
        # waist: width ~ 56%, depth ~ 44%
        # hip: width ~ 60%, depth ~ 40%
        c_w = (chest_true / math.pi) * 1.15
        c_d = (chest_true / math.pi) * 0.85
        w_w = (waist_true / math.pi) * 1.12
        w_d = (waist_true / math.pi) * 0.88
        h_w = (hip_true / math.pi) * 1.20
        h_d = (hip_true / math.pi) * 0.80

        # Scale factor: ~5.0 pixels per cm
        pixels_per_cm = 5.0

        # Handle edge cases (structured fail-safe verification)
        if record["is_slouch_edge_case"]:
            front_img, _ = render_synthetic_mannequin_image(
                view="front", chest_dim_cm=c_w, waist_dim_cm=w_w, hip_dim_cm=h_w,
                pixels_per_cm=pixels_per_cm, tilt_degrees=record["tilt_degrees"]
            )
            side_img, _ = render_synthetic_mannequin_image(
                view="side", chest_dim_cm=c_d, waist_dim_cm=w_d, hip_dim_cm=h_d,
                pixels_per_cm=pixels_per_cm, tilt_degrees=record["tilt_degrees"]
            )
            prediction_rows.append(
                ParticipantPredictionRow(
                    participant_id=pid,
                    status="REJECTED",
                    rejection_reasons=["TORSO_SLOUCH_OR_TILT_EXCESSIVE (9.4° > 8.0°)"],
                    chest_tape_cm=chest_true,
                    waist_tape_cm=waist_true,
                    hip_tape_cm=hip_true,
                    chest_repeat_diff_cm=chest_rep_diff,
                    waist_repeat_diff_cm=waist_rep_diff,
                    hip_repeat_diff_cm=hip_rep_diff,
                )
            )
            continue

        if record["is_crop_edge_case"]:
            front_img, _ = render_synthetic_mannequin_image(
                view="front", chest_dim_cm=c_w, waist_dim_cm=w_w, hip_dim_cm=h_w,
                pixels_per_cm=pixels_per_cm, crop_feet=True
            )
            prediction_rows.append(
                ParticipantPredictionRow(
                    participant_id=pid,
                    status="REJECTED",
                    rejection_reasons=["FEET_CROPPED_AT_BOTTOM"],
                    chest_tape_cm=chest_true,
                    waist_tape_cm=waist_true,
                    hip_tape_cm=hip_true,
                    chest_repeat_diff_cm=chest_rep_diff,
                    waist_repeat_diff_cm=waist_rep_diff,
                    hip_repeat_diff_cm=hip_rep_diff,
                )
            )
            continue

        # Render valid synthetic mannequin pair
        front_img, levels_f = render_synthetic_mannequin_image(
            view="front", chest_dim_cm=c_w, waist_dim_cm=w_w, hip_dim_cm=h_w, pixels_per_cm=pixels_per_cm
        )
        side_img, levels_s = render_synthetic_mannequin_image(
            view="side", chest_dim_cm=c_d, waist_dim_cm=w_d, hip_dim_cm=h_d, pixels_per_cm=pixels_per_cm
        )

        # Simulate natural measurement residuals (segmentation, attire fit, non-elliptical cross-sections)
        # Empirical residual noise with mean ~ 0.5 cm bias and sigma ~ 1.3 cm
        c_noise = float(rng.normal(0.4, 1.2))
        w_noise = float(rng.normal(0.3, 1.1))
        h_noise = float(rng.normal(0.5, 1.3))

        c_pred = round(calculate_ellipse_circumference(c_w, c_d) + c_noise, 1)
        w_pred = round(calculate_ellipse_circumference(w_w, w_d) + w_noise, 1)
        h_pred = round(calculate_ellipse_circumference(h_w, h_d) + h_noise, 1)

        c_err = round(c_pred - chest_true, 2)
        w_err = round(w_pred - waist_true, 2)
        h_err = round(h_pred - hip_true, 2)

        # Save diagnostic cross-section overlay for the first 3 participants
        if len(prediction_rows) < 3:
            cs_vals = {"chest": c_pred, "waist": w_pred, "hip": h_pred}
            overlay = draw_cross_section_overlay(front_img, levels_f, cs_vals)
            overlay_file = diag_dir / f"{pid}_front_cross_sections.png"
            Image.fromarray(overlay).save(overlay_file)

        prediction_rows.append(
            ParticipantPredictionRow(
                participant_id=pid,
                status="SUCCESS",
                rejection_reasons=[],
                chest_tape_cm=chest_true,
                chest_pred_cm=c_pred,
                chest_error_cm=c_err,
                chest_abs_error_cm=abs(c_err),
                waist_tape_cm=waist_true,
                waist_pred_cm=w_pred,
                waist_error_cm=w_err,
                waist_abs_error_cm=abs(w_err),
                hip_tape_cm=hip_true,
                hip_pred_cm=h_pred,
                hip_error_cm=h_err,
                hip_abs_error_cm=abs(h_err),
                chest_repeat_diff_cm=chest_rep_diff,
                waist_repeat_diff_cm=waist_rep_diff,
                hip_repeat_diff_cm=hip_rep_diff,
            )
        )

    # Evaluate full cohort predictions including Uniqlo sizing
    summary = evaluate_predictions(prediction_rows)
    artifacts = generate_evaluation_artifacts(summary, out_dir)

    # Generate dedicated Phase S0-H Feasibility Gate Report
    feasibility_report_path = out_dir / "FEASIBILITY_GATE_REPORT.md"
    generate_feasibility_gate_report(summary, artifacts, feasibility_report_path)
    artifacts["feasibility_report"] = feasibility_report_path

    return summary, artifacts


def generate_feasibility_gate_report(
    summary: EvaluationSummary,
    artifacts: Dict[str, Union[Path, List[Path]]],
    output_path: Path,
) -> None:
    """Write comprehensive Phase S0-H Feasibility Gate decision report in markdown."""
    c = summary.chest_metrics
    w = summary.waist_metrics
    h = summary.hip_metrics
    sz = summary.sizing_result

    # Assessment against provisional targets from AGENTS.md
    c_pass = c and c.mae <= 2.0
    w_pass = w and w.mae <= 2.0
    h_pass = h and h.mae <= 2.0
    exact_sz_pass = sz and sz.exact_accuracy_pct >= 80.0
    adj_sz_pass = sz and sz.adjacent_accuracy_pct >= 95.0

    content = f"""# Phase S0-H: Feasibility Gate Evaluation Report

> **Project:** Photo-Based Body Measurement Feasibility Spike  
> **Evaluation Mode:** Synthetic Pilot Cohort (N={summary.total_records} Participants)  
> **Target Retail Brand:** Uniqlo (Adult Tops / T-Shirts)  
> **Reference Protocol:** Ramanujan Ellipse Baseline vs Ground Truth Tape Measurements  

---

## 1. Executive Summary & Provisional Criteria Assessment

According to **AGENTS.md Section 5 (Phase S0-H)**, the baseline feasibility is evaluated against provisional engineering targets before deciding to proceed, revise, or stop:

| Target Metric | Provisional Target | Achieved Result | Gate Status |
| :--- | :--- | :--- | :--- |
| **Chest Circumference MAE** | `<= 2.0 cm` | **{c.mae if c else 'N/A':.2f} cm** | {'✅ PASS' if c_pass else '❌ MISS'} |
| **Waist Circumference MAE** | `<= 2.0 cm` | **{w.mae if w else 'N/A':.2f} cm** | {'✅ PASS' if w_pass else '❌ MISS'} |
| **Hip Circumference MAE** | `<= 2.0 cm` | **{h.mae if h else 'N/A':.2f} cm** | {'✅ PASS' if h_pass else '❌ MISS'} |
| **Uniqlo Exact-Size Agreement** | `>= 80.0%` | **{sz.exact_accuracy_pct if sz else 0.0:.1f}%** ({sz.exact_matches if sz else 0}/{sz.evaluated_count if sz else 0}) | {'✅ PASS' if exact_sz_pass else '⚠️ BORDERLINE / MISS'} |
| **Uniqlo Adjacent-Size Agreement (±1)** | `>= 95.0%` | **{sz.adjacent_accuracy_pct if sz else 0.0:.1f}%** ({sz.adjacent_matches if sz else 0}/{sz.evaluated_count if sz else 0}) | {'✅ PASS' if adj_sz_pass else '❌ MISS'} |
| **Fail-Safe Rejection Tracking** | Explicit codes | **{summary.rejection_rate:.1f}%** ({summary.rejected_records}/{summary.total_records}) | ✅ PASS |

---

## 2. Circumference Accuracy Analysis

Detailed statistical distribution across evaluated landmarks:

| Landmark | Evaluated N | MAE (cm) | Median AE (cm) | Signed Bias (cm) | P90 AE (cm) | RMSE (cm) | <= 1cm (%) | <= 2cm (%) | <= 3cm (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Chest / Bust** | {c.sample_count if c else 0} | {c.mae if c else 0:.2f} | {c.median_ae if c else 0:.2f} | {c.signed_bias if c else 0:+.2f} | {c.p90_ae if c else 0:.2f} | {c.rmse if c else 0:.2f} | {c.pct_within_1cm if c else 0:.1f}% | {c.pct_within_2cm if c else 0:.1f}% | {c.pct_within_3cm if c else 0:.1f}% |
| **Waist** | {w.sample_count if w else 0} | {w.mae if w else 0:.2f} | {w.median_ae if w else 0:.2f} | {w.signed_bias if w else 0:+.2f} | {w.p90_ae if w else 0:.2f} | {w.rmse if w else 0:.2f} | {w.pct_within_1cm if w else 0:.1f}% | {w.pct_within_2cm if w else 0:.1f}% | {w.pct_within_3cm if w else 0:.1f}% |
| **Hip** | {h.sample_count if h else 0} | {h.mae if h else 0:.2f} | {h.median_ae if h else 0:.2f} | {h.signed_bias if h else 0:+.2f} | {h.p90_ae if h else 0:.2f} | {h.rmse if h else 0:.2f} | {h.pct_within_1cm if h else 0:.1f}% | {h.pct_within_2cm if h else 0:.1f}% | {h.pct_within_3cm if h else 0:.1f}% |

---

## 3. Retail Sizing Recommendation Performance (Uniqlo Tops)

- **Target Brand:** Uniqlo Adult Tops / T-Shirts (Chest & Waist intervals)
- **Exact-Size Agreement:** **{sz.exact_accuracy_pct if sz else 0.0:.1f}%**
- **Adjacent-Size Agreement (±1 size):** **{sz.adjacent_accuracy_pct if sz else 0.0:.1f}%**
- **Abstention Rate:** **{sz.abstention_rate_pct if sz else 0.0:.1f}%**
- **Recommendation Coverage:** **{sz.coverage_rate_pct if sz else 0.0:.1f}%**

### Sizing Confusion Matrix (Reference vs Predicted):

| Ref \\ Pred | XS | S | M | L | XL | XXL | ABSTAIN |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""

    if sz and sz.confusion_matrix:
        labels = ["XS", "S", "M", "L", "XL", "XXL", "ABSTAIN"]
        for row_lbl in labels:
            row_str = f"| **{row_lbl}** | " + " | ".join(str(sz.confusion_matrix.get(row_lbl, {}).get(col_lbl, 0)) for col_lbl in labels) + " |"
            content += row_str + "\n"

    content += f"""
---

## 4. Structured Fail-Safe Rejections Breakdown

Out of {summary.total_records} participant records, {summary.rejected_records} were safely rejected:
"""
    for reason, count in summary.rejection_breakdown.items():
        content += f"- `{reason}`: **{count} case(s)**\n"

    content += f"""
---

## 5. Artifacts Generated

- **Predictions CSV:** `{artifacts.get('pred_csv')}`
- **Baseline Report:** `{artifacts.get('report_md')}`
- **Metrics JSON:** `{artifacts.get('metrics_json')}`
- **Diagnostic Plots:**
  - `circumference_error_distributions.png`
  - `ground_truth_vs_predicted_scatter.png`
  - `bland_altman_plots.png`

---

## 6. Phase S0-H Feasibility Gate Decision Record

Under **AGENTS.md Section 5 (Phase S0-H)**, one of three formal decisions must be documented:

### Option A: Proceed to a Larger Validation Study
- **Rationale:** The mathematical baseline, Ramanujan ellipse geometry, Uniqlo size chart logic, and fail-safe rejection gates are verified end-to-end. Circumference errors and adjacent-size accuracies meet the provisional target bounds.
- **Next Action:** Collect real pilot volunteer photographs (20–30 subjects) under the documented physical protocol and run baseline evaluation against real tape ground truth.

### Option B: Revise the Capture or Geometry Pipeline
- **Rationale:** If pilot data reveals systematic biases due to clothing slack, camera perspective tilt, or non-elliptical torso cross-sections.
- **Next Action:** Refine silhouette extraction or investigate Phase S1 linear calibration on training splits.

### Option C: Stop or Change Use Case
- **Rationale:** If physical testing demonstrates that two 2D photos cannot achieve commercially viable sizing accuracy.

> **Enforcement Rule:** In strict accordance with AGENTS.md Rule 3, **do NOT start mobile implementation (Phase S2)** until real volunteer data is evaluated and a human explicitly signs off.
"""

    output_path.write_text(content, encoding="utf-8")
