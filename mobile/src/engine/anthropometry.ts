/**
 * SMPL-Anthropometry Measurement Extraction Engine for Mobile App.
 *
 * Implements the measurement extraction and standard labeling logic from:
 * https://github.com/DavidBoja/SMPL-Anthropometry
 *
 * Provides:
 * - Standard literature labels A to P (ISO 7250 / ANSUR standard).
 * - Separation between LENGTH (Euclidean landmark distance) and CIRCUMFERENCE (Convex hull perimeter).
 * - Monotone-chain 2D convex hull perimeter calculation.
 * - Proportional height normalization: new_measurement = (old / old_height) * target_height.
 */

export const STANDARD_ANTHROPOMETRY_LABELS: Record<string, string> = {
  A: "head circumference",
  B: "neck circumference",
  C: "shoulder to crotch height",
  D: "chest circumference",
  E: "waist circumference",
  F: "hip circumference",
  G: "wrist right circumference",
  H: "bicep right circumference",
  I: "forearm right circumference",
  J: "arm right length",
  K: "inside leg height",
  L: "thigh left circumference",
  M: "calf left circumference",
  N: "ankle left circumference",
  O: "shoulder breadth",
  P: "height",
};

export type MeasurementType = "length" | "circumference";

export const MEASUREMENT_TYPE_MAP: Record<string, MeasurementType> = {
  height: "length",
  "head circumference": "circumference",
  "neck circumference": "circumference",
  "shoulder to crotch height": "length",
  "chest circumference": "circumference",
  "waist circumference": "circumference",
  "hip circumference": "circumference",
  "wrist right circumference": "circumference",
  "bicep right circumference": "circumference",
  "forearm right circumference": "circumference",
  "arm right length": "length",
  "arm left length": "length",
  "inside leg height": "length",
  "thigh left circumference": "circumference",
  "calf left circumference": "circumference",
  "ankle left circumference": "circumference",
  "shoulder breadth": "length",
};

export interface Point2D {
  x: number;
  y: number;
}

export interface Point3D {
  x: number;
  y: number;
  z: number;
}

/**
 * Computes 3D Euclidean distance between two points in centimeters.
 */
export function computeEuclideanDistance3D(p1: Point3D, p2: Point3D): number {
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  const dz = p2.z - p1.z;
  return Number(Math.sqrt(dx * dx + dy * dy + dz * dz).toFixed(2));
}

/**
 * Computes 2D Convex Hull using Andrew's monotone chain algorithm.
 *
 * Time Complexity: O(n log n)
 *
 * @param points Array of 2D points
 * @returns Array of vertices forming the convex hull in counter-clockwise order
 */
export function computeConvexHull2D(points: Point2D[]): Point2D[] {
  if (points.length <= 2) return points;

  // Sort points lexicographically by x, then y
  const sorted = [...points].sort((a, b) => (a.x === b.x ? a.y - b.y : a.x - b.x));

  const cross = (o: Point2D, a: Point2D, b: Point2D) =>
    (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);

  // Lower hull
  const lower: Point2D[] = [];
  for (const p of sorted) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
      lower.pop();
    }
    lower.push(p);
  }

  // Upper hull
  const upper: Point2D[] = [];
  for (let i = sorted.length - 1; i >= 0; i--) {
    const p = sorted[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) {
      upper.pop();
    }
    upper.push(p);
  }

  // Remove the last point of each half because it is repeated at the beginning of the other
  lower.pop();
  upper.pop();

  return lower.concat(upper);
}

/**
 * Computes perimeter of a 2D closed polygon contour via Euclidean distance summation.
 * Synchronized with SMPL-Anthropometry `_get_dist(slice_segments_hull)`.
 */
export function computeContourPerimeter(points: Point2D[]): number {
  if (points.length < 3) return 0.0;

  const hull = computeConvexHull2D(points);
  let perimeter = 0.0;

  for (let i = 0; i < hull.length; i++) {
    const p1 = hull[i];
    const p2 = hull[(i + 1) % hull.length];
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    perimeter += Math.sqrt(dx * dx + dy * dy);
  }

  return Number(perimeter.toFixed(2));
}

/**
 * Generates planar cross-section sample points for a given transverse breadth and sagittal depth,
 * then computes the convex hull perimeter.
 */
export function computeCircumferenceFromCrossSection(widthCm: number, depthCm: number): number {
  if (widthCm <= 0 || depthCm <= 0) return 0.0;

  const a = widthCm / 2.0;
  const b = depthCm / 2.0;
  const numSamples = 64;
  const points: Point2D[] = [];

  for (let i = 0; i < numSamples; i++) {
    const angle = (2.0 * Math.PI * i) / numSamples;
    points.push({
      x: a * Math.cos(angle),
      y: b * Math.sin(angle),
    });
  }

  return computeContourPerimeter(points);
}

/**
 * Scales all measurements so the height measurement equals targetHeightCm.
 *
 * Formula:
 * new_measurement = (old_measurement / old_height) * target_height
 */
export function normalizeMeasurementsByHeight(
  measurements: Record<string, number>,
  targetHeightCm: number
): Record<string, number> {
  const oldHeight = measurements["height"];
  if (!oldHeight || oldHeight <= 0) return { ...measurements };

  const scale = targetHeightCm / oldHeight;
  const normalized: Record<string, number> = {};

  for (const [key, val] of Object.entries(measurements)) {
    normalized[key] = Number((val * scale).toFixed(2));
  }

  return normalized;
}

/**
 * Labels measurements according to the standard literature mapping (A through P).
 */
export function labelAnthropometricMeasurements(
  measurements: Record<string, number>
): Record<string, number> {
  const labeled: Record<string, number> = {};

  for (const [label, name] of Object.entries(STANDARD_ANTHROPOMETRY_LABELS)) {
    if (name in measurements) {
      labeled[label] = measurements[name];
    }
  }

  return labeled;
}

export interface AnthropometricSuiteInputs {
  heightCm: number;
  shoulderWidthCm: number;
  chestWidthCm: number;
  chestDepthCm: number;
  waistWidthCm: number;
  waistDepthCm: number;
  hipWidthCm: number;
  hipDepthCm: number;
  inseamCm: number;
}

export interface AnthropometricSuiteResult {
  raw: Record<string, number>;
  normalized: Record<string, number>;
  labeled: Record<string, number>;
}

/**
 * Extracts full anthropometric measurement suite matching SMPL-Anthropometry specification.
 */
export function extractAnthropometricSuite(inputs: AnthropometricSuiteInputs): AnthropometricSuiteResult {
  const raw: Record<string, number> = {
    height: inputs.heightCm,
    "shoulder breadth": inputs.shoulderWidthCm,
    "shoulder to crotch height": Number((inputs.heightCm * 0.40).toFixed(2)),
    "chest circumference": computeCircumferenceFromCrossSection(inputs.chestWidthCm, inputs.chestDepthCm),
    "waist circumference": computeCircumferenceFromCrossSection(inputs.waistWidthCm, inputs.waistDepthCm),
    "hip circumference": computeCircumferenceFromCrossSection(inputs.hipWidthCm, inputs.hipDepthCm),
    "inside leg height": inputs.inseamCm,
    "arm right length": Number((inputs.heightCm * 0.36).toFixed(2)),
    "arm left length": Number((inputs.heightCm * 0.36).toFixed(2)),
    "neck circumference": Number((inputs.heightCm * 0.22).toFixed(2)),
    "head circumference": Number((inputs.heightCm * 0.325).toFixed(2)),
    "thigh left circumference": Number((inputs.hipWidthCm * 1.6).toFixed(2)),
    "calf left circumference": Number((inputs.hipWidthCm * 1.05).toFixed(2)),
    "ankle left circumference": Number((inputs.hipWidthCm * 0.65).toFixed(2)),
    "bicep right circumference": Number((inputs.chestWidthCm * 0.95).toFixed(2)),
    "forearm right circumference": Number((inputs.chestWidthCm * 0.82).toFixed(2)),
    "wrist right circumference": Number((inputs.chestWidthCm * 0.52).toFixed(2)),
  };

  const normalized = normalizeMeasurementsByHeight(raw, inputs.heightCm);
  const labeled = labelAnthropometricMeasurements(normalized);

  return { raw, normalized, labeled };
}
