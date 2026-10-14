/**
 * Scale Calibration Module for Mobile Reference Engine.
 *
 * Converts pixel measurements to centimeters using entered height.
 * Enforces quality constraints:
 * - Stature sanity checks (50 to 260 cm).
 * - Minimum pixel span (> 50 pixels).
 * - Torso pitch tilt threshold (<= 8.0 degrees).
 * - Front/side scale consistency check (discrepancy <= 5%).
 *
 * Synchronized with body_measurement.scale_calibration.
 */

import { PairScaleResult, ScaleCalibrationResult } from "../types";

export const MIN_HEIGHT_CM = 100.0;
export const MAX_HEIGHT_CM = 230.0;
export const MIN_BODY_SPAN_PIXELS = 50;
export const MAX_TORSO_TILT_DEGREES = 8.0;
export const MAX_PAIR_SCALE_DISCREPANCY_FRACTION = 0.05; // 5%

/**
 * Calibrates scale from entered height and detected vertical body span.
 *
 * @param enteredHeightCm Stature entered by user in cm.
 * @param bodySpanPixels Vertical pixel span from crown/vertex to bottom of feet.
 * @param torsoTiltDegrees Pitch tilt angle of torso relative to vertical.
 * @param topY Crown Y pixel coordinate.
 * @param bottomY Foot sole Y pixel coordinate.
 * @param imageHeight Total image pixel height.
 * @param method Detection method used ("hybrid", "pose", "mask").
 */
export function calibrateScaleFromSpan(
  enteredHeightCm: number,
  bodySpanPixels: number,
  torsoTiltDegrees: number = 0.0,
  topY: number = 0,
  bottomY: number = 0,
  imageHeight: number = 1000,
  method: string = "hybrid"
): ScaleCalibrationResult {
  const rejections: string[] = [];

  if (
    !Number.isFinite(enteredHeightCm) ||
    enteredHeightCm < MIN_HEIGHT_CM ||
    enteredHeightCm > MAX_HEIGHT_CM
  ) {
    rejections.push(
      `Entered height (${enteredHeightCm}cm) outside valid anthropometric range [${MIN_HEIGHT_CM}, ${MAX_HEIGHT_CM}].`
    );
  }

  if (
    !Number.isFinite(bodySpanPixels) ||
    bodySpanPixels < MIN_BODY_SPAN_PIXELS
  ) {
    rejections.push(
      `Detected body span (${bodySpanPixels}px) is too small (<${MIN_BODY_SPAN_PIXELS}px).`
    );
  }

  if (Math.abs(torsoTiltDegrees) > MAX_TORSO_TILT_DEGREES) {
    rejections.push(
      `Torso tilt angle (${torsoTiltDegrees.toFixed(1)}°) exceeds maximum allowed (${MAX_TORSO_TILT_DEGREES.toFixed(1)}°).`
    );
  }

  const isValid = rejections.length === 0;
  const pixelsPerCm = isValid ? bodySpanPixels / enteredHeightCm : 0;
  const cmPerPixel = isValid ? enteredHeightCm / bodySpanPixels : 0;

  return {
    pixelsPerCm: Number(pixelsPerCm.toFixed(4)),
    cmPerPixel: Number(cmPerPixel.toFixed(4)),
    enteredHeightCm,
    bodySpanPixels,
    bounds: {
      topY,
      bottomY,
      spanPixels: bodySpanPixels,
      imageHeight,
      method,
      reliable: isValid,
    },
    torsoTiltDegrees,
    isValid,
    rejectionReasons: rejections,
  };
}

/**
 * Verifies that front and side captures were taken at consistent camera distance and zoom.
 *
 * Discrepancy = |front_scale - side_scale| / mean_scale
 * Must be <= 5% (0.05).
 */
export function verifyPairScaleConsistency(
  frontScale: ScaleCalibrationResult,
  sideScale: ScaleCalibrationResult,
  maxDiscrepancy: number = MAX_PAIR_SCALE_DISCREPANCY_FRACTION
): PairScaleResult {
  const rejections: string[] = [];

  if (!frontScale.isValid) {
    rejections.push(...frontScale.rejectionReasons.map((r) => `FRONT_${r}`));
  }
  if (!sideScale.isValid) {
    rejections.push(...sideScale.rejectionReasons.map((r) => `SIDE_${r}`));
  }

  if (!frontScale.isValid || !sideScale.isValid) {
    return {
      isValid: false,
      discrepancyFraction: 1.0,
      rejectionReasons: rejections,
    };
  }

  const meanScale = (frontScale.pixelsPerCm + sideScale.pixelsPerCm) / 2.0;
  if (meanScale <= 0) {
    return {
      isValid: false,
      discrepancyFraction: 1.0,
      rejectionReasons: ["Mean scale is zero or negative."],
    };
  }

  const discrepancy = Math.abs(frontScale.pixelsPerCm - sideScale.pixelsPerCm) / meanScale;

  if (discrepancy > maxDiscrepancy) {
    rejections.push(
      `Scale discrepancy between front (${frontScale.pixelsPerCm} px/cm) and side (${sideScale.pixelsPerCm} px/cm) is ${(discrepancy * 100).toFixed(1)}%, exceeding allowed ${(maxDiscrepancy * 100).toFixed(1)}% threshold. Ensure phone distance remains identical.`
    );
  }

  return {
    isValid: rejections.length === 0,
    discrepancyFraction: Number(discrepancy.toFixed(4)),
    rejectionReasons: rejections,
  };
}
