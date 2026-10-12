import { calibrateMeasurement, CALIBRATION_SPECS } from "../src/engine/calibrationModels";

describe("Phase S1 Ridge Regression Calibration Engine", () => {
  test("chest calibration at feature means yields exact intercept", () => {
    const spec = CALIBRATION_SPECS.chest;
    const meanRamanujan = spec.scalerMean[0];
    const meanHeight = spec.scalerMean[1];
    const meanWeight = spec.scalerMean[2];

    const res = calibrateMeasurement("chest", meanRamanujan, meanHeight, meanWeight);
    expect(res.isCalibrated).toBe(true);
    expect(res.rawRamanujanCm).toBe(meanRamanujan);
    // When features = mean, all z-scores = 0, so prediction = intercept
    expect(res.calibratedCm).toBe(Number(spec.intercept.toFixed(2)));
  });

  test("waist calibration at feature means yields exact intercept", () => {
    const spec = CALIBRATION_SPECS.waist;
    const meanRamanujan = spec.scalerMean[0];
    const meanHeight = spec.scalerMean[1];
    const meanWeight = spec.scalerMean[2];

    const res = calibrateMeasurement("waist", meanRamanujan, meanHeight, meanWeight);
    expect(res.isCalibrated).toBe(true);
    expect(res.rawRamanujanCm).toBe(meanRamanujan);
    expect(res.calibratedCm).toBe(Number(spec.intercept.toFixed(2)));
  });

  test("handles missing weight by falling back to cohort prior mean", () => {
    const spec = CALIBRATION_SPECS.chest;
    const meanRamanujan = spec.scalerMean[0];
    const meanHeight = spec.scalerMean[1];

    // Omit weight (undefined)
    const res = calibrateMeasurement("chest", meanRamanujan, meanHeight);
    expect(res.isCalibrated).toBe(true);
    expect(res.calibratedCm).toBe(Number(spec.intercept.toFixed(2)));
    expect(res.notes).toContain("standard cohort prior weight");
  });

  test("rejects invalid circumference inputs safely", () => {
    const zeroCirc = calibrateMeasurement("chest", 0.0, 175.0, 70.0);
    expect(zeroCirc.isCalibrated).toBe(false);
    expect(zeroCirc.calibratedCm).toBe(0);

    const negCirc = calibrateMeasurement("waist", -10.0, 175.0, 70.0);
    expect(negCirc.isCalibrated).toBe(false);
    expect(negCirc.calibratedCm).toBe(0);
  });
});
