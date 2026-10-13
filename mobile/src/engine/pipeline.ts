/**
 * Mobile Pipeline Orchestrator.
 *
 * Runs scale calibration, cross-section extraction, Ramanujan circumferences,
 * Phase S1 Ridge regression models, and Uniqlo size chart recommendation.
 */

import { FullMeasurementEstimate } from "../types";
import { calibrateMeasurement } from "./calibrationModels";
import { computeCrossSection } from "./geometry";
import { calibrateScaleFromSpan, verifyPairScaleConsistency } from "./scaleCalibration";
import { recommendSize } from "./sizing";

export interface PipelineInputs {
  heightCm: number;
  weightKg?: number | null;
  front: {
    imageHeight: number;
    imageWidth: number;
    topY: number;
    bottomY: number;
    tiltDegrees?: number;
    chestWidthPx: number;
    waistWidthPx: number;
    hipWidthPx: number;
    chestYPx: number;
    waistYPx: number;
    hipYPx: number;
  };
  side: {
    imageHeight: number;
    imageWidth: number;
    topY: number;
    bottomY: number;
    tiltDegrees?: number;
    chestDepthPx: number;
    waistDepthPx: number;
    hipDepthPx: number;
    chestYPx: number;
    waistYPx: number;
    hipYPx: number;
  };
}

/**
 * Executes the complete measurement and sizing pipeline.
 */
export function runMeasurementPipeline(inputs: PipelineInputs): FullMeasurementEstimate {
  const rejections: string[] = [];

  // 1. Scale Calibration Front
  const frontSpan = inputs.front.bottomY - inputs.front.topY;
  const scaleFront = calibrateScaleFromSpan(
    inputs.heightCm,
    frontSpan,
    inputs.front.tiltDegrees || 0.0,
    inputs.front.topY,
    inputs.front.bottomY,
    inputs.front.imageHeight,
    "mobile_hybrid"
  );
  if (!scaleFront.isValid) {
    rejections.push(...scaleFront.rejectionReasons.map((r) => `FRONT_${r}`));
  }

  // 2. Scale Calibration Side
  const sideSpan = inputs.side.bottomY - inputs.side.topY;
  const scaleSide = calibrateScaleFromSpan(
    inputs.heightCm,
    sideSpan,
    inputs.side.tiltDegrees || 0.0,
    inputs.side.topY,
    inputs.side.bottomY,
    inputs.side.imageHeight,
    "mobile_hybrid"
  );
  if (!scaleSide.isValid) {
    rejections.push(...scaleSide.rejectionReasons.map((r) => `SIDE_${r}`));
  }

  // 3. Verify Distance / Scale Consistency between Front and Side
  const pairScale = verifyPairScaleConsistency(scaleFront, scaleSide);
  if (!pairScale.isValid) {
    rejections.push(...pairScale.rejectionReasons);
  }

  if (rejections.length > 0) {
    const emptySizing = recommendSize(null);
    return {
      chest: { rawRamanujanCm: 0, calibratedCm: 0, modelType: "None", isCalibrated: false, notes: "Scale calibration failed." },
      waist: { rawRamanujanCm: 0, calibratedCm: 0, modelType: "None", isCalibrated: false, notes: "Scale calibration failed." },
      hip: { rawRamanujanCm: 0, calibratedCm: 0, modelType: "None", isCalibrated: false, notes: "Scale calibration failed." },
      scaleFront,
      scaleSide,
      sizing: emptySizing,
      isValid: false,
      rejectionReasons: rejections,
    };
  }

  // 4. Compute Cross Sections
  const csChest = computeCrossSection(
    "chest",
    inputs.front.chestYPx,
    inputs.side.chestYPx,
    inputs.front.chestWidthPx,
    inputs.side.chestDepthPx,
    scaleFront,
    scaleSide
  );
  if (!csChest.isValid && csChest.rejectionReason) {
    rejections.push(csChest.rejectionReason);
  }

  const csWaist = computeCrossSection(
    "waist",
    inputs.front.waistYPx,
    inputs.side.waistYPx,
    inputs.front.waistWidthPx,
    inputs.side.waistDepthPx,
    scaleFront,
    scaleSide
  );
  if (!csWaist.isValid && csWaist.rejectionReason) {
    rejections.push(csWaist.rejectionReason);
  }

  const csHip = computeCrossSection(
    "hip",
    inputs.front.hipYPx,
    inputs.side.hipYPx,
    inputs.front.hipWidthPx,
    inputs.side.hipDepthPx,
    scaleFront,
    scaleSide
  );
  if (!csHip.isValid && csHip.rejectionReason) {
    rejections.push(csHip.rejectionReason);
  }

  if (rejections.length > 0) {
    const emptySizing = recommendSize(null);
    return {
      chest: { rawRamanujanCm: csChest.circumferenceCm, calibratedCm: 0, modelType: "None", isCalibrated: false, notes: "Cross-section invalid." },
      waist: { rawRamanujanCm: csWaist.circumferenceCm, calibratedCm: 0, modelType: "None", isCalibrated: false, notes: "Cross-section invalid." },
      hip: { rawRamanujanCm: csHip.circumferenceCm, calibratedCm: 0, modelType: "None", isCalibrated: false, notes: "Cross-section invalid." },
      scaleFront,
      scaleSide,
      sizing: emptySizing,
      isValid: false,
      rejectionReasons: rejections,
    };
  }

  // 5. Phase S1 Ridge Regression Calibration
  const calChest = calibrateMeasurement("chest", csChest.circumferenceCm, inputs.heightCm, inputs.weightKg);
  const calWaist = calibrateMeasurement("waist", csWaist.circumferenceCm, inputs.heightCm, inputs.weightKg);
  // Hip baseline Ramanujan (exploratory / direct)
  const calHip = {
    rawRamanujanCm: csHip.circumferenceCm,
    calibratedCm: csHip.circumferenceCm,
    modelType: "Ramanujan_Baseline",
    isCalibrated: false,
    notes: "Direct Ramanujan ellipse geometry.",
  };

  // 6. Retail Sizing Recommendation (Uniqlo Adult Tops)
  const sizing = recommendSize(calChest.calibratedCm, calWaist.calibratedCm);

  return {
    chest: calChest,
    waist: calWaist,
    hip: calHip,
    scaleFront,
    scaleSide,
    sizing,
    isValid: true,
    rejectionReasons: [],
  };
}
