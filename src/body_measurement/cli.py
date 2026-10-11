"""Command line interface and batch processor for pose detection and segmentation."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from body_measurement.diagnostics import create_diagnostic_overlay
from body_measurement.image_io import load_and_validate_image
from body_measurement.pose_detection import PoseDetector
from body_measurement.quality_checks import evaluate_pose_quality
from body_measurement.schemas import ParticipantRecord, load_participant_manifest


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


def main():
    """Command-line entry point for running pose detection batch jobs."""
    parser = argparse.ArgumentParser(description="MediaPipe Pose Detection & Segmentation Batch Processor")
    parser.add_argument("--manifest", type=str, help="Path to participant CSV manifest")
    parser.add_argument("--front", type=str, help="Path to single front image")
    parser.add_argument("--side", type=str, help="Path to single side image")
    parser.add_argument("--output-dir", type=str, default="outputs", help="Directory for diagnostic overlays and JSON reports")
    parser.add_argument("--model-path", type=str, default="models/pose_landmarker_full.task", help="Path to Pose Landmarker .task model")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.manifest:
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
