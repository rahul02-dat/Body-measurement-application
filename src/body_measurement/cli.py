"""Command line interface and batch processor for pose detection and segmentation."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from body_measurement.diagnostics import create_diagnostic_overlay, draw_cross_section_overlay
from body_measurement.evaluation import (
    ParticipantPredictionRow,
    evaluate_predictions,
    generate_evaluation_artifacts,
)
from body_measurement.image_io import load_and_validate_image
from body_measurement.measurement_geometry import compute_body_measurements
from body_measurement.pose_detection import PoseDetector
from body_measurement.quality_checks import evaluate_pose_quality
from body_measurement.scale_calibration import calibrate_scale, verify_pair_scale_consistency
from body_measurement.schemas import ParticipantRecord, load_participant_manifest
from body_measurement.segmentation import extract_binary_mask


def process_image_view(
    image_path: Union[str, Path],
    view_name: str,
    detector: PoseDetector,
    output_dir: Optional[Path] = None,
    participant_id: str = "SAMPLE",
) -> Dict[str, Any]:
    """Process a single image view (front or side) through detection, quality check, and overlays."""
    loaded_img = load_and_validate_image(image_path)
    detection = detector.detect(loaded_img)
    quality_report = evaluate_pose_quality(detection)

    overlay_path = None
    if output_dir is not None:
        diag_dir = output_dir / "diagnostics"
        diag_dir.mkdir(parents=True, exist_ok=True)
        overlay_filename = f"{participant_id}_{view_name}_overlay.png"
        overlay_path = diag_dir / overlay_filename
        create_diagnostic_overlay(
            image=loaded_img,
            detection=detection,
            quality_report=quality_report,
            output_path=overlay_path,
            title=f"ID: {participant_id} | View: {view_name.upper()}",
        )

    # Serialize landmarks summary
    landmarks_summary = []
    for lm in detection.landmarks:
        landmarks_summary.append({
            "index": lm.index,
            "name": lm.name,
            "x": round(lm.x, 4),
            "y": round(lm.y, 4),
            "z": round(lm.z, 4),
            "visibility": round(lm.visibility, 3),
            "presence": round(lm.presence, 3),
        })

    return {
        "view": view_name,
        "image_path": str(image_path),
        "has_pose": detection.has_pose,
        "num_poses_detected": detection.num_poses_detected,
        "is_valid": quality_report.is_valid,
        "rejection_reasons": quality_report.rejection_reasons,
        "mean_landmark_visibility": quality_report.mean_landmark_visibility,
        "head_visible": quality_report.head_visible,
        "feet_visible": quality_report.feet_visible,
        "torso_visible": quality_report.torso_visible,
        "top_margin_fraction": quality_report.top_margin_fraction,
        "bottom_margin_fraction": quality_report.bottom_margin_fraction,
        "diagnostic_overlay_path": str(overlay_path) if overlay_path else None,
        "landmarks_count": len(detection.landmarks),
        "landmarks": landmarks_summary,
    }


def process_participant_record(
    record: ParticipantRecord,
    detector: PoseDetector,
    base_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Process both front and side views for a participant record."""
    root = base_dir or Path.cwd()
    front_path = root / record.front_image_path
    side_path = root / record.side_image_path

    front_res = process_image_view(
        image_path=front_path,
        view_name="front",
        detector=detector,
        output_dir=output_dir,
        participant_id=record.participant_id,
    )
    side_res = process_image_view(
        image_path=side_path,
        view_name="side",
        detector=detector,
        output_dir=output_dir,
        participant_id=record.participant_id,
    )

    both_valid = front_res["is_valid"] and side_res["is_valid"]
    combined_rejections = []
    if not front_res["is_valid"]:
        combined_rejections.extend([f"FRONT_{r}" for r in front_res["rejection_reasons"]])
    if not side_res["is_valid"]:
        combined_rejections.extend([f"SIDE_{r}" for r in side_res["rejection_reasons"]])

    return {
        "participant_id": record.participant_id,
        "overall_valid": both_valid,
        "rejection_reasons": combined_rejections,
        "front": front_res,
        "side": side_res,
    }


def run_batch_manifest(
    manifest_csv: Union[str, Path],
    output_dir: Union[str, Path],
    base_dir: Optional[Union[str, Path]] = None,
    model_path: Union[str, Path] = "models/pose_landmarker_full.task",
) -> List[Dict[str, Any]]:
    """Run batch pose detection and segmentation over a manifest CSV."""
    records = load_participant_manifest(manifest_csv, verify_images_exist=True, base_dir=base_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    with PoseDetector(model_asset_path=model_path) as detector:
        for record in records:
            res = process_participant_record(
                record=record,
                detector=detector,
                base_dir=Path(base_dir) if base_dir else None,
                output_dir=out_dir,
            )
            results.append(res)

    summary_file = out_dir / "pose_batch_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


def evaluate_manifest(
    manifest_csv: Union[str, Path],
    output_dir: Union[str, Path] = "reports",
    base_dir: Optional[Union[str, Path]] = None,
    model_path: Union[str, Path] = "models/pose_landmarker_full.task",
):
    """
    Execute end-to-end evaluation comparing image estimates with tape ground truth.
    Generates markdown report, per-participant error CSV, metrics JSON, and diagnostic plots.
    """
    records = load_participant_manifest(manifest_csv, verify_images_exist=False, base_dir=base_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    root = Path(base_dir) if base_dir else Path.cwd()

    prediction_rows: List[ParticipantPredictionRow] = []

    with PoseDetector(model_asset_path=model_path) as detector:
        for record in records:
            front_path = root / record.front_image_path
            side_path = root / record.side_image_path

            if not front_path.is_file() or not side_path.is_file():
                prediction_rows.append(
                    ParticipantPredictionRow(
                        participant_id=record.participant_id,
                        status="REJECTED",
                        rejection_reasons=["IMAGE_FILE_NOT_FOUND_ON_DISK"],
                        chest_tape_cm=record.effective_chest_tape_cm,
                        waist_tape_cm=record.effective_waist_tape_cm,
                        hip_tape_cm=record.effective_hip_tape_cm,
                        chest_repeat_diff_cm=record.chest_rep_diff_cm,
                        waist_repeat_diff_cm=record.waist_rep_diff_cm,
                        hip_repeat_diff_cm=record.hip_rep_diff_cm,
                    )
                )
                continue

            try:
                front_img = load_and_validate_image(front_path)
                side_img = load_and_validate_image(side_path)

                f_det = detector.detect(front_img)
                s_det = detector.detect(side_img)

                f_qual = evaluate_pose_quality(f_det)
                s_qual = evaluate_pose_quality(s_det)

                rejections = []
                if not f_qual.is_valid:
                    rejections.extend([f"FRONT_{r}" for r in f_qual.rejection_reasons])
                if not s_qual.is_valid:
                    rejections.extend([f"SIDE_{r}" for r in s_qual.rejection_reasons])

                f_mask = extract_binary_mask(f_det.segmentation_mask) if f_det.segmentation_mask is not None else np.zeros((front_img.height, front_img.width), dtype=np.uint8)
                s_mask = extract_binary_mask(s_det.segmentation_mask) if s_det.segmentation_mask is not None else np.zeros((side_img.height, side_img.width), dtype=np.uint8)

                f_scale = calibrate_scale(record.height_cm, f_det, f_mask)
                s_scale = calibrate_scale(record.height_cm, s_det, s_mask)

                pair_scale = verify_pair_scale_consistency(f_scale, s_scale)
                if not pair_scale.is_valid:
                    rejections.extend(pair_scale.rejection_reasons)

                if rejections:
                    prediction_rows.append(
                        ParticipantPredictionRow(
                            participant_id=record.participant_id,
                            status="REJECTED",
                            rejection_reasons=rejections,
                            chest_tape_cm=record.effective_chest_tape_cm,
                            waist_tape_cm=record.effective_waist_tape_cm,
                            hip_tape_cm=record.effective_hip_tape_cm,
                            chest_repeat_diff_cm=record.chest_rep_diff_cm,
                            waist_repeat_diff_cm=record.waist_rep_diff_cm,
                            hip_repeat_diff_cm=record.hip_rep_diff_cm,
                        )
                    )
                    continue

                geo_res = compute_body_measurements(
                    front_detection=f_det,
                    front_mask=f_mask,
                    front_scale=f_scale,
                    side_detection=s_det,
                    side_mask=s_mask,
                    side_scale=s_scale,
                )

                if not geo_res.is_valid:
                    prediction_rows.append(
                        ParticipantPredictionRow(
                            participant_id=record.participant_id,
                            status="REJECTED",
                            rejection_reasons=geo_res.rejection_reasons,
                            chest_tape_cm=record.effective_chest_tape_cm,
                            waist_tape_cm=record.effective_waist_tape_cm,
                            hip_tape_cm=record.effective_hip_tape_cm,
                            chest_repeat_diff_cm=record.chest_rep_diff_cm,
                            waist_repeat_diff_cm=record.waist_rep_diff_cm,
                            hip_repeat_diff_cm=record.hip_rep_diff_cm,
                        )
                    )
                    continue

                # Successful estimation
                c_true = record.effective_chest_tape_cm
                w_true = record.effective_waist_tape_cm
                h_true = record.effective_hip_tape_cm

                c_pred = geo_res.chest.circumference_cm
                w_pred = geo_res.waist.circumference_cm
                h_pred = geo_res.hip.circumference_cm

                prediction_rows.append(
                    ParticipantPredictionRow(
                        participant_id=record.participant_id,
                        status="SUCCESS",
                        rejection_reasons=[],
                        chest_tape_cm=c_true,
                        chest_pred_cm=c_pred,
                        chest_error_cm=round(c_pred - c_true, 2),
                        chest_abs_error_cm=round(abs(c_pred - c_true), 2),
                        waist_tape_cm=w_true,
                        waist_pred_cm=w_pred,
                        waist_error_cm=round(w_pred - w_true, 2),
                        waist_abs_error_cm=round(abs(w_pred - w_true), 2),
                        hip_tape_cm=h_true,
                        hip_pred_cm=h_pred,
                        hip_error_cm=round(h_pred - h_true, 2),
                        hip_abs_error_cm=round(abs(h_pred - h_true), 2),
                        chest_repeat_diff_cm=record.chest_rep_diff_cm,
                        waist_repeat_diff_cm=record.waist_rep_diff_cm,
                        hip_repeat_diff_cm=record.hip_repeat_diff_cm,
                    )
                )

                # Save cross-section overlay
                diag_dir = out_dir / "diagnostics"
                diag_dir.mkdir(parents=True, exist_ok=True)
                cs_front = {
                    "chest": geo_res.chest.front_y_px,
                    "waist": geo_res.waist.front_y_px,
                    "hip": geo_res.hip.front_y_px,
                }
                cs_vals = {
                    "chest": c_pred,
                    "waist": w_pred,
                    "hip": h_pred,
                }
                overlay_front = draw_cross_section_overlay(front_img.rgb_array, cs_front, cs_vals)
                overlay_path = diag_dir / f"{record.participant_id}_front_cross_sections.png"
                from PIL import Image as PILImage
                PILImage.fromarray(overlay_front).save(overlay_path)

            except Exception as e:
                prediction_rows.append(
                    ParticipantPredictionRow(
                        participant_id=record.participant_id,
                        status="REJECTED",
                        rejection_reasons=[f"PIPELINE_EXCEPTION: {e}"],
                        chest_tape_cm=record.effective_chest_tape_cm,
                        waist_tape_cm=record.effective_waist_tape_cm,
                        hip_tape_cm=record.effective_hip_tape_cm,
                    )
                )

    summary = evaluate_predictions(prediction_rows)
    artifacts = generate_evaluation_artifacts(summary, out_dir)
    return summary, artifacts


def main():
    """Command-line entry point for running pose detection and evaluation batch jobs."""
    parser = argparse.ArgumentParser(description="MediaPipe Pose Detection & Evaluation Batch Processor")
    parser.add_argument("--evaluate-manifest", type=str, help="Run end-to-end evaluation against a participant CSV manifest")
    parser.add_argument("--manifest", type=str, help="Path to participant CSV manifest for pose batch processing")
    parser.add_argument("--front", type=str, help="Path to single front image")
    parser.add_argument("--side", type=str, help="Path to single side image")
    parser.add_argument("--run-synthetic-demo", action="store_true", help="Execute complete Phase S0-H synthetic feasibility pilot demo (N=25)")
    parser.add_argument("--output-dir", type=str, default="reports", help="Directory for reports, plots, and diagnostic overlays")
    parser.add_argument("--base-dir", type=str, default=None, help="Base directory to resolve image paths against")
    parser.add_argument("--model-path", type=str, default="models/pose_landmarker_full.task", help="Path to Pose Landmarker .task model")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.run_synthetic_demo:
        from body_measurement.synthetic_demo import run_synthetic_feasibility_pipeline
        summary, artifacts = run_synthetic_feasibility_pipeline(output_dir=out_dir)
        print("=" * 60)
        print("SYNTHETIC FEASIBILITY DEMO COMPLETED SUCCESSFULLY")
        print(f"Total Cohort: {summary.total_records} | Success: {summary.successful_records} | Rejected: {summary.rejected_records}")
        print(f"Feasibility Gate Report: {artifacts['feasibility_report']}")
        print(f"Baseline Report Markdown: {artifacts['report_md']}")
        print(f"Predictions CSV:         {artifacts['pred_csv']}")
        print(f"Metrics JSON:            {artifacts['metrics_json']}")
        print(f"Diagnostic Plots:        {len(artifacts['plots'])} plot(s) generated")
        print("=" * 60)
    elif args.evaluate_manifest:
        summary, artifacts = evaluate_manifest(
            manifest_csv=args.evaluate_manifest,
            output_dir=out_dir,
            base_dir=args.base_dir,
            model_path=args.model_path,
        )
        print("=" * 60)
        print("EVALUATION COMPLETED SUCCESSFULLY")
        print(f"Total Records: {summary.total_records} | Success: {summary.successful_records} | Rejected: {summary.rejected_records}")
        print(f"Report Markdown: {artifacts['report_md']}")
        print(f"Predictions CSV: {artifacts['pred_csv']}")
        print(f"Metrics JSON:    {artifacts['metrics_json']}")
        print(f"Diagnostic Plots: {len(artifacts['plots'])} plot(s) generated")
        print("=" * 60)
    elif args.manifest:
        results = run_batch_manifest(
            manifest_csv=args.manifest,
            output_dir=out_dir,
            model_path=args.model_path,
        )
        print(f"Processed {len(results)} participant records from manifest.")
        print(f"Summary written to: {out_dir / 'pose_batch_summary.json'}")
    elif args.front and args.side:
        with PoseDetector(model_asset_path=args.model_path) as detector:
            front_res = process_image_view(args.front, "front", detector, output_dir=out_dir)
            side_res = process_image_view(args.side, "side", detector, output_dir=out_dir)
            combined = {
                "front": front_res,
                "side": side_res,
                "both_valid": front_res["is_valid"] and side_res["is_valid"],
            }
            summary_path = out_dir / "single_pair_summary.json"
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(combined, f, indent=2)
            print(f"Processed single pair. Summary written to {summary_path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

