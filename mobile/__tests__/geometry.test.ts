import { calculateEllipseCircumference, computeCrossSection } from "../src/engine/geometry";
import { ScaleCalibrationResult } from "../src/types";

describe("Ramanujan Ellipse Geometry Engine", () => {
  test("circle special case matches 2*pi*r exactly", () => {
    // Diameter = 20.0 cm -> radius = 10.0 cm -> circumference = 2 * pi * 10 = 62.83 cm
    const circ = calculateEllipseCircumference(20.0, 20.0);
    expect(circ).toBe(62.83);
  });

  test("known analytical ellipse matches Python reference value", () => {
    // Semi-axes: a = 5.0 (width = 10.0), b = 3.0 (depth = 6.0)
    // Ramanujan formula yields 25.53 cm
    const circ = calculateEllipseCircumference(10.0, 6.0);
    expect(circ).toBe(25.53);
  });

  test.each([
    [0.0, 10.0],
    [10.0, 0.0],
    [-5.0, 10.0],
    [10.0, -5.0],
    [NaN, 10.0],
    [10.0, Infinity],
  ])("invalid inputs (%p, %p) throw Error", (w, d) => {
    expect(() => calculateEllipseCircumference(w, d)).toThrow();
  });

  test("computeCrossSection correctly extracts slice dimensions", () => {
    const dummyScale: ScaleCalibrationResult = {
      pixelsPerCm: 5.0,
      cmPerPixel: 0.2,
      enteredHeightCm: 175.0,
      bodySpanPixels: 875,
      bounds: {
        topY: 50,
        bottomY: 925,
        spanPixels: 875,
        imageHeight: 1000,
        method: "test",
        reliable: true,
      },
      torsoTiltDegrees: 0.0,
      isValid: true,
      rejectionReasons: [],
    };

    // Width = 100px (20.0 cm), Depth = 80px (16.0 cm)
    const slice = computeCrossSection(
      "waist",
      450,
      450,
      100,
      80,
      dummyScale,
      dummyScale
    );

    expect(slice.isValid).toBe(true);
    expect(slice.widthCm).toBe(20.0);
    expect(slice.depthCm).toBe(16.0);
    expect(slice.circumferenceCm).toBe(calculateEllipseCircumference(20.0, 16.0));
    expect(slice.aspectRatio).toBe(1.25);
  });

  test("computeCrossSection handles zero width or depth safely", () => {
    const dummyScale: ScaleCalibrationResult = {
      pixelsPerCm: 5.0,
      cmPerPixel: 0.2,
      enteredHeightCm: 175.0,
      bodySpanPixels: 875,
      bounds: {
        topY: 50,
        bottomY: 925,
        spanPixels: 875,
        imageHeight: 1000,
        method: "test",
        reliable: true,
      },
      torsoTiltDegrees: 0.0,
      isValid: true,
      rejectionReasons: [],
    };

    const sliceZeroWidth = computeCrossSection("chest", 300, 300, 0, 80, dummyScale, dummyScale);
    expect(sliceZeroWidth.isValid).toBe(false);
    expect(sliceZeroWidth.rejectionReason).toContain("Zero or negative pixel width");

    const sliceZeroDepth = computeCrossSection("chest", 300, 300, 100, 0, dummyScale, dummyScale);
    expect(sliceZeroDepth.isValid).toBe(false);
    expect(sliceZeroDepth.rejectionReason).toContain("Zero or negative pixel depth");
  });
});
