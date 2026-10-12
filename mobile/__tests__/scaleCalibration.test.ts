import {
  calibrateScaleFromSpan,
  verifyPairScaleConsistency,
} from "../src/engine/scaleCalibration";

describe("Scale Calibration Engine", () => {
  test("valid span correctly calculates scale conversion", () => {
    // 175.0 cm subject spanning 875 pixels -> 5.0 px/cm, 0.20 cm/px
    const res = calibrateScaleFromSpan(175.0, 875, 0.0);
    expect(res.isValid).toBe(true);
    expect(res.pixelsPerCm).toBe(5.0);
    expect(res.cmPerPixel).toBe(0.2);
    expect(res.rejectionReasons).toHaveLength(0);
  });

  test("out of bounds height is rejected", () => {
    const tooShort = calibrateScaleFromSpan(40.0, 500);
    expect(tooShort.isValid).toBe(false);
    expect(tooShort.rejectionReasons[0]).toContain("outside valid anthropometric range");

    const tooTall = calibrateScaleFromSpan(300.0, 1500);
    expect(tooTall.isValid).toBe(false);
    expect(tooTall.rejectionReasons[0]).toContain("outside valid anthropometric range");
  });

  test("small body span is rejected", () => {
    const tinySpan = calibrateScaleFromSpan(175.0, 30);
    expect(tinySpan.isValid).toBe(false);
    expect(tinySpan.rejectionReasons[0]).toContain("Detected body span (30px) is too small");
  });

  test("excessive torso tilt is rejected", () => {
    const tilted = calibrateScaleFromSpan(175.0, 875, 9.5);
    expect(tilted.isValid).toBe(false);
    expect(tilted.rejectionReasons[0]).toContain("Torso tilt angle (9.5°) exceeds maximum allowed (8.0°)");
  });

  test("verifyPairScaleConsistency approves matching scales", () => {
    const front = calibrateScaleFromSpan(175.0, 875, 0.0); // 5.00 px/cm
    const side = calibrateScaleFromSpan(175.0, 860, 0.0); // 4.9143 px/cm (discrepancy ~ 1.7%)
    const pair = verifyPairScaleConsistency(front, side);

    expect(pair.isValid).toBe(true);
    expect(pair.discrepancyFraction).toBeLessThan(0.05);
    expect(pair.rejectionReasons).toHaveLength(0);
  });

  test("verifyPairScaleConsistency rejects divergent camera distances (>5%)", () => {
    const front = calibrateScaleFromSpan(175.0, 875, 0.0); // 5.00 px/cm
    const side = calibrateScaleFromSpan(175.0, 750, 0.0); // 4.2857 px/cm (discrepancy ~ 15.3%)
    const pair = verifyPairScaleConsistency(front, side);

    expect(pair.isValid).toBe(false);
    expect(pair.discrepancyFraction).toBeGreaterThan(0.05);
    expect(pair.rejectionReasons[0]).toContain("exceeding allowed 5.0% threshold");
  });
});
