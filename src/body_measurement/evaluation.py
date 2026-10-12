"""Statistical evaluation comparing image-derived estimates with physical tape measurements."""

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import numpy as np

from body_measurement.sizing import (
    SizingEvaluationResult,
    evaluate_sizing_performance,
    recommend_size,
    UNIQLO_ADULT_TOPS_CHART,
)


@dataclass
class MeasurementMetrics:
    """Comprehensive statistical error metrics for a single anatomical measurement."""

    name: str
    sample_count: int
    mae: float
    median_ae: float
    signed_bias: float
    p90_ae: float
    rmse: float
    pct_within_1cm: float
    pct_within_2cm: float
    pct_within_3cm: float
    pct_within_5cm: float


@dataclass
class RepeatVariabilityMetrics:
    """Intra-rater tape repeat measurement variability metrics."""

    name: str
    sample_count: int
    mean_abs_diff: float
    max_abs_diff: float
    std_diff: float


@dataclass
class ParticipantPredictionRow:
    """Row record capturing tape ground truth, prediction, errors, and rejection details."""

    participant_id: str
    status: str  # "SUCCESS" or "REJECTED"
    rejection_reasons: List[str] = field(default_factory=list)
    chest_tape_cm: Optional[float] = None
    chest_pred_cm: Optional[float] = None
    chest_error_cm: Optional[float] = None
    chest_abs_error_cm: Optional[float] = None
    waist_tape_cm: Optional[float] = None
    waist_pred_cm: Optional[float] = None
    waist_error_cm: Optional[float] = None
    waist_abs_error_cm: Optional[float] = None
    hip_tape_cm: Optional[float] = None
    hip_pred_cm: Optional[float] = None
    hip_error_cm: Optional[float] = None
    hip_abs_error_cm: Optional[float] = None
    chest_repeat_diff_cm: Optional[float] = None
    waist_repeat_diff_cm: Optional[float] = None
    hip_repeat_diff_cm: Optional[float] = None
    ref_size: Optional[str] = None
    pred_size: Optional[str] = None
    is_size_exact: Optional[bool] = None
    is_size_adjacent: Optional[bool] = None


@dataclass
class EvaluationSummary:
    """Consolidated dataset-level evaluation summary."""

    total_records: int
    successful_records: int
    rejected_records: int
    rejection_rate: float
    rejection_breakdown: Dict[str, int]
    chest_metrics: Optional[MeasurementMetrics] = None
    waist_metrics: Optional[MeasurementMetrics] = None
    hip_metrics: Optional[MeasurementMetrics] = None
    repeat_variability: Dict[str, RepeatVariabilityMetrics] = field(default_factory=dict)
    sizing_result: Optional[SizingEvaluationResult] = None
    predictions: List[ParticipantPredictionRow] = field(default_factory=list)


def calculate_measurement_metrics(
    name: str,
    y_true: List[float],
    y_pred: List[float],
) -> MeasurementMetrics:
    """
    Calculate MAE, Median AE, signed bias, 90th percentile AE, RMSE,
    and proportions within +/-1cm, +/-2cm, +/-3cm, and +/-5cm bands.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: {len(y_true)} ground-truth vs {len(y_pred)} predictions.")
    if len(y_true) == 0:
        return MeasurementMetrics(
            name=name, sample_count=0, mae=0.0, median_ae=0.0, signed_bias=0.0,
            p90_ae=0.0, rmse=0.0, pct_within_1cm=0.0, pct_within_2cm=0.0,
            pct_within_3cm=0.0, pct_within_5cm=0.0,
        )

    errors = np.array(y_pred, dtype=float) - np.array(y_true, dtype=float)
    abs_errors = np.abs(errors)
    n = len(errors)

    mae = float(np.mean(abs_errors))
    median_ae = float(np.median(abs_errors))
    signed_bias = float(np.mean(errors))
    p90_ae = float(np.percentile(abs_errors, 90))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    pct_1cm = float(np.count_nonzero(abs_errors <= 1.0) / n * 100.0)
    pct_2cm = float(np.count_nonzero(abs_errors <= 2.0) / n * 100.0)
    pct_3cm = float(np.count_nonzero(abs_errors <= 3.0) / n * 100.0)
    pct_5cm = float(np.count_nonzero(abs_errors <= 5.0) / n * 100.0)

    return MeasurementMetrics(
        name=name,
        sample_count=n,
        mae=round(mae, 2),
        median_ae=round(median_ae, 2),
        signed_bias=round(signed_bias, 2),
        p90_ae=round(p90_ae, 2),
        rmse=round(rmse, 2),
        pct_within_1cm=round(pct_1cm, 1),
        pct_within_2cm=round(pct_2cm, 1),
        pct_within_3cm=round(pct_3cm, 1),
        pct_within_5cm=round(pct_5cm, 1),
    )


def calculate_repeat_variability(
    name: str,
    repeat_diffs: List[float],
) -> RepeatVariabilityMetrics:
    """Calculate intra-rater repeat reading variability metrics."""
    valid_diffs = [abs(d) for d in repeat_diffs if d is not None and math.isfinite(d)]
    if not valid_diffs:
        return RepeatVariabilityMetrics(name=name, sample_count=0, mean_abs_diff=0.0, max_abs_diff=0.0, std_diff=0.0)

    arr = np.array(valid_diffs, dtype=float)
    return RepeatVariabilityMetrics(
        name=name,
        sample_count=len(arr),
        mean_abs_diff=round(float(np.mean(arr)), 2),
        max_abs_diff=round(float(np.max(arr)), 2),
        std_diff=round(float(np.std(arr)), 2),
    )


import math


def evaluate_predictions(predictions: List[ParticipantPredictionRow]) -> EvaluationSummary:
    """Aggregate per-participant rows into a complete EvaluationSummary."""
    total = len(predictions)
    successful = [p for p in predictions if p.status == "SUCCESS"]
    rejected = [p for p in predictions if p.status != "SUCCESS"]

    rejection_breakdown: Dict[str, int] = {}
    for r in rejected:
        for reason in r.rejection_reasons:
            rejection_breakdown[reason] = rejection_breakdown.get(reason, 0) + 1

    # Extract paired measurements for successful runs
    chest_true = [p.chest_tape_cm for p in successful if p.chest_tape_cm and p.chest_pred_cm]
    chest_pred = [p.chest_pred_cm for p in successful if p.chest_tape_cm and p.chest_pred_cm]

    waist_true = [p.waist_tape_cm for p in successful if p.waist_tape_cm and p.waist_pred_cm]
    waist_pred = [p.waist_pred_cm for p in successful if p.waist_tape_cm and p.waist_pred_cm]

    hip_true = [p.hip_tape_cm for p in successful if p.hip_tape_cm and p.hip_pred_cm]
    hip_pred = [p.hip_pred_cm for p in successful if p.hip_tape_cm and p.hip_pred_cm]

    chest_metrics = calculate_measurement_metrics("chest", chest_true, chest_pred) if chest_true else None
    waist_metrics = calculate_measurement_metrics("waist", waist_true, waist_pred) if waist_true else None
    hip_metrics = calculate_measurement_metrics("hip", hip_true, hip_pred) if hip_true else None

    # Repeat variability
    repeat_metrics = {
        "chest": calculate_repeat_variability("chest", [p.chest_repeat_diff_cm for p in predictions if p.chest_repeat_diff_cm is not None]),
        "waist": calculate_repeat_variability("waist", [p.waist_repeat_diff_cm for p in predictions if p.waist_repeat_diff_cm is not None]),
        "hip": calculate_repeat_variability("hip", [p.hip_repeat_diff_cm for p in predictions if p.hip_repeat_diff_cm is not None]),
    }

    # Sizing evaluation (Uniqlo Adult Tops / T-Shirts)
    sizing_comparisons = []
    for p in predictions:
        if p.chest_tape_cm is not None:
            sizing_comparisons.append({
                "participant_id": p.participant_id,
                "ref_chest_cm": p.chest_tape_cm,
                "ref_waist_cm": p.waist_tape_cm,
                "pred_chest_cm": p.chest_pred_cm,
                "pred_waist_cm": p.waist_pred_cm,
            })

    sizing_result = evaluate_sizing_performance(sizing_comparisons, chart=UNIQLO_ADULT_TOPS_CHART) if sizing_comparisons else None

    # Update prediction rows with sizing metadata
    if sizing_result:
        sizing_map = {item["participant_id"]: item for item in sizing_result.participant_comparisons}
        for p in predictions:
            if p.participant_id in sizing_map:
                s_info = sizing_map[p.participant_id]
                p.ref_size = s_info["ref_size"]
                p.pred_size = s_info["pred_size"]
                p.is_size_exact = s_info["is_exact"]
                p.is_size_adjacent = s_info["is_adjacent"]

    rejection_rate = round((len(rejected) / total * 100.0), 1) if total > 0 else 0.0

    return EvaluationSummary(
        total_records=total,
        successful_records=len(successful),
        rejected_records=len(rejected),
        rejection_rate=rejection_rate,
        rejection_breakdown=rejection_breakdown,
        chest_metrics=chest_metrics,
        waist_metrics=waist_metrics,
        hip_metrics=hip_metrics,
        repeat_variability=repeat_metrics,
        sizing_result=sizing_result,
        predictions=predictions,
    )


def generate_diagnostic_plots(summary: EvaluationSummary, output_dir: Path) -> List[Path]:
    """Generate Matplotlib diagnostic figures (scatter, error distributions, Bland-Altman)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: List[Path] = []

    successful = [p for p in summary.predictions if p.status == "SUCCESS"]
    if not successful:
        return generated

    measurements = [
        ("Chest", [p.chest_tape_cm for p in successful], [p.chest_pred_cm for p in successful]),
        ("Waist", [p.waist_tape_cm for p in successful], [p.waist_pred_cm for p in successful]),
        ("Hip", [p.hip_tape_cm for p in successful], [p.hip_pred_cm for p in successful]),
    ]

    # 1. Tape vs Predicted Scatter Plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, (label, y_true, y_pred) in zip(axes, measurements):
        valid_pairs = [(t, p) for t, p in zip(y_true, y_pred) if t is not None and p is not None]
        if not valid_pairs:
            continue
        ts, ps = zip(*valid_pairs)
        min_v = min(min(ts), min(ps)) - 5
        max_v = max(max(ts), max(ps)) + 5

        ax.scatter(ts, ps, color="#2980b9", alpha=0.8, edgecolors="k", s=50)
        ax.plot([min_v, max_v], [min_v, max_v], "r--", label="1:1 Identity")
        ax.fill_between([min_v, max_v], [min_v - 2, max_v - 2], [min_v + 2, max_v + 2], color="gray", alpha=0.15, label="±2cm Band")
        ax.set_title(f"{label}: Tape vs Predicted")
        ax.set_xlabel("Tape Ground Truth (cm)")
        ax.set_ylabel("Image Predicted (cm)")
        ax.set_xlim(min_v, max_v)
        ax.set_ylim(min_v, max_v)
        ax.legend(loc="upper left")
        ax.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    scatter_path = output_dir / "tape_vs_predicted_scatter.png"
    plt.savefig(scatter_path, dpi=200)
    plt.close()
    generated.append(scatter_path)

    # 2. Signed Error Distribution Histograms
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, (label, y_true, y_pred) in zip(axes, measurements):
        errors = [p - t for t, p in zip(y_true, y_pred) if t is not None and p is not None]
        if not errors:
            continue
        ax.hist(errors, bins=10, color="#27ae60", edgecolor="black", alpha=0.7)
        ax.axvline(0.0, color="red", linestyle="--", label="Zero Bias")
        mean_err = np.mean(errors)
        ax.axvline(mean_err, color="orange", linestyle="-", label=f"Bias: {mean_err:+.1f}cm")
        ax.set_title(f"{label} Signed Error Distribution")
        ax.set_xlabel("Error: Pred - Tape (cm)")
        ax.set_ylabel("Count")
        ax.legend()
        ax.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    hist_path = output_dir / "error_distribution_histograms.png"
    plt.savefig(hist_path, dpi=200)
    plt.close()
    generated.append(hist_path)

    # 3. Bland-Altman Plots
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, (label, y_true, y_pred) in zip(axes, measurements):
        valid = [(t, p) for t, p in zip(y_true, y_pred) if t is not None and p is not None]
        if not valid:
            continue
        means = [(t + p) / 2.0 for t, p in valid]
        diffs = [p - t for t, p in valid]
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs)

        ax.scatter(means, diffs, color="#8e44ad", alpha=0.8, edgecolors="k", s=50)
        ax.axhline(mean_diff, color="red", linestyle="-", label=f"Mean: {mean_diff:+.1f}cm")
        ax.axhline(mean_diff + 1.96 * std_diff, color="gray", linestyle="--", label=f"+1.96 SD: {mean_diff + 1.96*std_diff:+.1f}cm")
        ax.axhline(mean_diff - 1.96 * std_diff, color="gray", linestyle="--", label=f"-1.96 SD: {mean_diff - 1.96*std_diff:+.1f}cm")
        ax.set_title(f"{label} Bland-Altman")
        ax.set_xlabel("Mean of Tape & Predicted (cm)")
        ax.set_ylabel("Difference: Pred - Tape (cm)")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    ba_path = output_dir / "bland_altman_plots.png"
    plt.savefig(ba_path, dpi=200)
    plt.close()
    generated.append(ba_path)

    return generated


def export_predictions_csv(predictions: List[ParticipantPredictionRow], output_path: Path):
    """Save machine-readable CSV of per-participant predictions and errors."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "participant_id", "status", "rejection_reasons",
        "chest_tape_cm", "chest_pred_cm", "chest_error_cm", "chest_abs_error_cm",
        "waist_tape_cm", "waist_pred_cm", "waist_error_cm", "waist_abs_error_cm",
        "hip_tape_cm", "hip_pred_cm", "hip_error_cm", "hip_abs_error_cm",
        "chest_repeat_diff_cm", "waist_repeat_diff_cm", "hip_repeat_diff_cm",
        "ref_size", "pred_size", "is_size_exact", "is_size_adjacent",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in predictions:
            row = asdict(p)
            row["rejection_reasons"] = "; ".join(p.rejection_reasons)
            writer.writerow(row)


def generate_markdown_report(summary: EvaluationSummary, output_path: Path, plot_paths: Optional[List[Path]] = None):
    """Write human-readable Markdown baseline evaluation report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = [
        "# Feasibility Spike Baseline Evaluation Report",
        "",
        "> **Notice:** Experimental evaluation comparing photo-based Ramanujan ellipse approximations against physical tape measurements.",
        "",
        "## 1. Evaluation Sample Counts & Quality Overview",
        "",
        f"- **Total Manifest Records:** {summary.total_records}",
        f"- **Successful Estimates:** {summary.successful_records}",
        f"- **Rejected Records:** {summary.rejected_records} ({summary.rejection_rate}% failure/rejection rate)",
        "",
    ]

    if summary.rejection_breakdown:
        lines.append("### Failure / Rejection Reasons Breakdown:")
        for reason, count in sorted(summary.rejection_breakdown.items(), key=lambda x: -x[1]):
            lines.append(f"- `{reason}`: {count} case(s)")
        lines.append("")

    lines.extend([
        "## 2. Circumference Accuracy Metrics",
        "",
        "| Anatomical Landmark | Evaluated N | MAE (cm) | Median AE (cm) | Signed Bias (cm) | P90 AE (cm) | RMSE (cm) | <= 1cm (%) | <= 2cm (%) (Target) | <= 3cm (%) | <= 5cm (%) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for m in [summary.chest_metrics, summary.waist_metrics, summary.hip_metrics]:
        if m and m.sample_count > 0:
            lines.append(
                f"| **{m.name.capitalize()}** | {m.sample_count} | {m.mae:.2f} | {m.median_ae:.2f} | {m.signed_bias:+.2f} | {m.p90_ae:.2f} | {m.rmse:.2f} | {m.pct_within_1cm:.1f}% | **{m.pct_within_2cm:.1f}%** | {m.pct_within_3cm:.1f}% | {m.pct_within_5cm:.1f}% |"
            )
        elif m:
            lines.append(f"| **{m.name.capitalize()}** | 0 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |")

    lines.extend([
        "",
        "## 3. Intra-Rater Tape Measurement Variability",
        "",
        "| Measurement | Sample Count | Mean Abs Diff (cm) | Max Abs Diff (cm) | Std Diff (cm) |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ])
    for name, r in summary.repeat_variability.items():
        if r.sample_count > 0:
            lines.append(f"| **{name.capitalize()}** | {r.sample_count} | {r.mean_abs_diff:.2f} | {r.max_abs_diff:.2f} | {r.std_diff:.2f} |")
        else:
            lines.append(f"| **{name.capitalize()}** | 0 | N/A | N/A | N/A |")

    # Section 4: Sizing Recommendation Evaluation
    if summary.sizing_result:
        sr = summary.sizing_result
        lines.extend([
            "",
            "## 4. Garment Size-Chart Recommendation Evaluation",
            "",
            f"- **Target Brand:** {sr.chart_brand}",
            f"- **Garment Category:** {sr.chart_category}",
            f"- **Exact-Size Agreement:** **{sr.exact_accuracy_pct:.1f}%** ({sr.exact_matches}/{sr.evaluated_count}) [Provisional Target: >= 80%]",
            f"- **Adjacent-Size Agreement (±1 size):** **{sr.adjacent_accuracy_pct:.1f}%** ({sr.exact_matches + sr.adjacent_matches}/{sr.evaluated_count}) [Provisional Target: >= 95%]",
            f"- **Abstention Rate:** {sr.abstention_rate_pct:.1f}% ({sr.abstention_count}/{sr.total_participants})",
            f"- **Recommendation Coverage:** {sr.coverage_rate_pct:.1f}%",
            "",
            "### Size Recommendation Confusion Matrix (Reference vs Predicted):",
            "",
        ])

        labels = UNIQLO_ADULT_TOPS_CHART.ordered_sizes + ["ABSTAIN"]
        header = "| Ref \\ Pred | " + " | ".join(labels) + " |"
        sep = "| :--- | " + " | ".join([":---"] * len(labels)) + " |"
        lines.append(header)
        lines.append(sep)

        for ref_lbl in labels:
            row_counts = [str(sr.confusion_matrix.get(ref_lbl, {}).get(pred_lbl, 0)) for pred_lbl in labels]
            lines.append(f"| **{ref_lbl}** | " + " | ".join(row_counts) + " |")

    lines.extend([
        "",
        "## 5. Key Limitations & Assumptions Disclosed",
        "",
        "1. **Ramanujan Ellipse Model:** Real human body cross-sections are irregular non-elliptical geometries; approximating them with orthogonal widths and depths creates an inherent geometric modeling error.",
        "2. **Attire & Slack:** Clothing thickness or fabric bunching introduces radial bias into the silhouette boundary.",
        "3. **Height Scale Anchor:** Calibration is entirely scaled by user-reported height. Incorrect height entries directly scale all circumferences proportionally.",
        "4. **Perspective & Pose Inconsistency:** Camera pitch tilt, subject distance variations, and stance shifts between front and side photos induce projection distortion.",
        "",
    ])

    if plot_paths:
        lines.append("## 6. Diagnostic Error Plots")
        lines.append("")
        for p in plot_paths:
            lines.append(f"- **{p.stem.replace('_', ' ').capitalize()}:** `file://{p.resolve()}`")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def generate_evaluation_artifacts(
    summary: EvaluationSummary,
    output_dir: Union[str, Path],
) -> Dict[str, Path]:
    """Generate all evaluation reports, CSVs, JSONs, and plot figures."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"

    plots = generate_diagnostic_plots(summary, plots_dir)

    report_md = out_dir / "baseline_evaluation_report.md"
    generate_markdown_report(summary, report_md, plot_paths=plots)

    pred_csv = out_dir / "per_participant_predictions.csv"
    export_predictions_csv(summary.predictions, pred_csv)

    metrics_json = out_dir / "metrics_summary.json"
    summary_dict = {
        "total_records": summary.total_records,
        "successful_records": summary.successful_records,
        "rejected_records": summary.rejected_records,
        "rejection_rate": summary.rejection_rate,
        "rejection_breakdown": summary.rejection_breakdown,
        "chest": asdict(summary.chest_metrics) if summary.chest_metrics else None,
        "waist": asdict(summary.waist_metrics) if summary.waist_metrics else None,
        "hip": asdict(summary.hip_metrics) if summary.hip_metrics else None,
        "repeat_variability": {k: asdict(v) for k, v in summary.repeat_variability.items()},
        "sizing": asdict(summary.sizing_result) if summary.sizing_result else None,
    }
    with open(metrics_json, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)

    return {
        "report_md": report_md,
        "pred_csv": pred_csv,
        "metrics_json": metrics_json,
        "plots": plots,
    }
