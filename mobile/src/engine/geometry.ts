/**
 * Ramanujan Ellipse Circumference Approximation and Cross-Section Calculations.
 *
 * Implements Ramanujan's First-Order Ellipse Formula:
 * a = width_cm / 2
 * b = depth_cm / 2
 * C ≈ π * [ 3*(a + b) - sqrt((3*a + b) * (a + 3*b)) ]
 *
 * Exact match with Python reference engine: body_measurement.measurement_geometry
 */

import { CrossSectionSlice, ScaleCalibrationResult } from "../types";

/**
 * Calculates ellipse circumference using Ramanujan's first-order approximation.
 *
 * @param widthCm Horizontal transverse breadth in cm (must be > 0 and finite).
 * @param depthCm Sagittal anterior-posterior depth in cm (must be > 0 and finite).
 * @returns Circumference in centimeters rounded to 2 decimal places.
 * @throws Error if width or depth is non-positive or non-finite.
 */
export function calculateEllipseCircumference(widthCm: number, depthCm: number): number {
  if (
    !Number.isFinite(widthCm) ||
    !Number.isFinite(depthCm) ||
    widthCm <= 0 ||
    depthCm <= 0
  ) {
    throw new Error(
      `Invalid ellipse dimensions: width=${widthCm}, depth=${depthCm}. Must be positive finite numbers.`
    );
  }

  // Exact circle special case (width == depth)
  if (Math.abs(widthCm - depthCm) < 1e-9) {
    const radius = widthCm / 2.0;
    return Number((2.0 * Math.PI * radius).toFixed(2));
  }

  const a = widthCm / 2.0;
  const b = depthCm / 2.0;

  // Ramanujan first-order formula:
  // C ≈ π * ( 3*(a + b) - sqrt( (3*a + b) * (a + 3*b) ) )
  const term1 = 3.0 * (a + b);
  const term2 = Math.sqrt((3.0 * a + b) * (a + 3.0 * b));
  const circumference = Math.PI * (term1 - term2);

  return Number(circumference.toFixed(2));
}

/**
 * Computes a single cross-section slice from pixel widths and calibrated scales.
 *
 * @param name Landmark name ("chest", "waist", "hip")
 * @param frontYPx Y row in front image
 * @param sideYPx Y row in side image
 * @param frontWidthPx Width in pixels across front silhouette
 * @param sideDepthPx Depth in pixels across side silhouette
 * @param frontScale Calibrated scale for front view
 * @param sideScale Calibrated scale for side view
 */
export function computeCrossSection(
  name: "chest" | "waist" | "hip",
  frontYPx: number,
  sideYPx: number,
  frontWidthPx: number,
  sideDepthPx: number,
  frontScale: ScaleCalibrationResult,
  sideScale: ScaleCalibrationResult
): CrossSectionSlice {
  if (frontWidthPx <= 0) {
    return {
      name,
      frontYPx,
      sideYPx,
      widthCm: 0,
      depthCm: 0,
      circumferenceCm: 0,
      aspectRatio: 0,
      isValid: false,
      rejectionReason: `Zero or negative pixel width (${frontWidthPx}px) at ${name} level.`,
    };
  }

  if (sideDepthPx <= 0) {
    return {
      name,
      frontYPx,
      sideYPx,
      widthCm: 0,
      depthCm: 0,
      circumferenceCm: 0,
      aspectRatio: 0,
      isValid: false,
      rejectionReason: `Zero or negative pixel depth (${sideDepthPx}px) at ${name} level.`,
    };
  }

  const widthCm = Number((frontWidthPx * frontScale.cmPerPixel).toFixed(2));
  const depthCm = Number((sideDepthPx * sideScale.cmPerPixel).toFixed(2));

  try {
    const circumferenceCm = calculateEllipseCircumference(widthCm, depthCm);
    const aspectRatio = Number((widthCm / depthCm).toFixed(3));

    return {
      name,
      frontYPx,
      sideYPx,
      widthCm,
      depthCm,
      circumferenceCm,
      aspectRatio,
      isValid: true,
    };
  } catch (err: any) {
    return {
      name,
      frontYPx,
      sideYPx,
      widthCm,
      depthCm,
      circumferenceCm: 0,
      aspectRatio: 0,
      isValid: false,
      rejectionReason: err.message || "Failed to calculate circumference.",
    };
  }
}
