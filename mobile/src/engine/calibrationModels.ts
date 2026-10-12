/**
 * Phase S1 Ridge Regression Calibration Engine for Mobile App.
 *
 * Embeds the weights trained on 6,068 subjects from the US Army Anthropometric Survey
 * (ANSUR II, Public Domain) to calibrate Ramanujan ellipse circumference estimates.
 *
 * Synchronized with models/calibration_models.json and body_measurement.calibration.
 */

import { CalibratedMeasurement } from "../types";

export interface RidgeModelSpec {
  modelType: string;
  alpha: number;
  features: string[];
  intercept: number;
  coefficients: number[];
  scalerMean: number[];
  scalerScale: number[];
}

export const CALIBRATION_SPECS: Record<"chest" | "waist", RidgeModelSpec> = {
  chest: {
    modelType: "RidgeRegression",
    alpha: 1.0,
    features: ["chest_ramanujan_cm", "height_cm", "weight_kg"],
    intercept: 102.21728471363824,
    coefficients: [5.386479349116646, -0.2916899893398617, 4.8059643268500825],
    scalerMean: [84.09715080346106, 171.40939431396785, 79.72855377008652],
    scalerScale: [6.601081882080323, 9.051515927680683, 15.755089055900195],
  },
  waist: {
    modelType: "RidgeRegression",
    alpha: 1.0,
    features: ["waist_ramanujan_cm", "height_cm", "weight_kg"],
    intercept: 91.4724557066337,
    coefficients: [10.585097578837246, -0.5523981264613593, 1.0972966381264422],
    scalerMean: [86.6054985578904, 171.40939431396785, 79.72855377008652],
    scalerScale: [10.906134236145325, 9.051515927680683, 15.755089055900195],
  },
};

/**
 * Calibrates a Ramanujan circumference measurement using the Phase S1 Ridge Regression model.
 *
 * @param landmark "chest" or "waist"
 * @param ramanujanCircumferenceCm Circumference from Ramanujan ellipse formula
 * @param heightCm Stature in cm
 * @param weightKg Optional weight in kg (if omitted, population mean weight 79.73kg is used)
 */
export function calibrateMeasurement(
  landmark: "chest" | "waist",
  ramanujanCircumferenceCm: number,
  heightCm: number,
  weightKg?: number | null
): CalibratedMeasurement {
  if (ramanujanCircumferenceCm <= 0 || !Number.isFinite(ramanujanCircumferenceCm)) {
    return {
      rawRamanujanCm: ramanujanCircumferenceCm,
      calibratedCm: 0,
      modelType: "None",
      isCalibrated: false,
      notes: "Invalid raw circumference input.",
    };
  }

  const spec = CALIBRATION_SPECS[landmark];
  const effectiveWeight = weightKg && weightKg > 0 ? weightKg : spec.scalerMean[2];

  // Standardize features: z = (x - mean) / scale
  const rawFeatures = [ramanujanCircumferenceCm, heightCm, effectiveWeight];
  let prediction = spec.intercept;

  for (let i = 0; i < rawFeatures.length; i++) {
    const z = (rawFeatures[i] - spec.scalerMean[i]) / spec.scalerScale[i];
    prediction += spec.coefficients[i] * z;
  }

  const rounded = Number(prediction.toFixed(2));
  const hasWeight = Boolean(weightKg && weightKg > 0);

  return {
    rawRamanujanCm: ramanujanCircumferenceCm,
    calibratedCm: rounded,
    modelType: "RidgeRegression_ANSUR_II",
    isCalibrated: true,
    notes: hasWeight
      ? `Calibrated with height (${heightCm}cm) and weight (${weightKg}kg).`
      : `Calibrated with height (${heightCm}cm) and standard cohort prior weight (${spec.scalerMean[2].toFixed(1)}kg).`,
  };
}
