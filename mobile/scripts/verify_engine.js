/**
 * Standalone Reference Engine Verification Script (Zero Dependencies).
 * Runs directly on Node.js to verify mathematical parity with the Python spike.
 */

const assert = require("assert");

// 1. Ramanujan Ellipse Formula
function calculateEllipseCircumference(widthCm, depthCm) {
  if (!Number.isFinite(widthCm) || !Number.isFinite(depthCm) || widthCm <= 0 || depthCm <= 0) {
    throw new Error("Invalid ellipse dimensions.");
  }
  if (Math.abs(widthCm - depthCm) < 1e-9) {
    return Number((2.0 * Math.PI * (widthCm / 2.0)).toFixed(2));
  }
  const a = widthCm / 2.0;
  const b = depthCm / 2.0;
  const term1 = 3.0 * (a + b);
  const term2 = Math.sqrt((3.0 * a + b) * (a + 3.0 * b));
  return Number((Math.PI * (term1 - term2)).toFixed(2));
}

// 2. Scale Calibration
function calibrateScale(enteredHeightCm, bodySpanPixels, tiltDegrees = 0.0) {
  const rejections = [];
  if (!Number.isFinite(enteredHeightCm) || enteredHeightCm < 50 || enteredHeightCm > 260) {
    rejections.push("Invalid height.");
  }
  if (!Number.isFinite(bodySpanPixels) || bodySpanPixels < 50) {
    rejections.push("Span too small.");
  }
  if (Math.abs(tiltDegrees) > 8.0) {
    rejections.push("Tilt exceeds 8 deg.");
  }
  const isValid = rejections.length === 0;
  return {
    pixelsPerCm: isValid ? Number((bodySpanPixels / enteredHeightCm).toFixed(4)) : 0,
    cmPerPixel: isValid ? Number((enteredHeightCm / bodySpanPixels).toFixed(4)) : 0,
    isValid,
    rejections,
  };
}

// 3. Pair Scale Consistency
function verifyPairScale(frontScale, sideScale) {
  if (!frontScale.isValid || !sideScale.isValid) return { isValid: false };
  const mean = (frontScale.pixelsPerCm + sideScale.pixelsPerCm) / 2.0;
  const discrepancy = Math.abs(frontScale.pixelsPerCm - sideScale.pixelsPerCm) / mean;
  return {
    isValid: discrepancy <= 0.05,
    discrepancy: Number(discrepancy.toFixed(4)),
  };
}

// 4. Ridge Calibration
const RIDGE_SPECS = {
  chest: {
    intercept: 102.21728471363824,
    coefficients: [5.386479349116646, -0.2916899893398617, 4.8059643268500825],
    scalerMean: [84.09715080346106, 171.40939431396785, 79.72855377008652],
    scalerScale: [6.601081882080323, 9.051515927680683, 15.755089055900195],
  },
  waist: {
    intercept: 91.4724557066337,
    coefficients: [10.585097578837246, -0.5523981264613593, 1.0972966381264422],
    scalerMean: [86.6054985578904, 171.40939431396785, 79.72855377008652],
    scalerScale: [10.906134236145325, 9.051515927680683, 15.755089055900195],
  },
};

function calibrateRidge(landmark, ramanujanCm, heightCm, weightKg) {
  const spec = RIDGE_SPECS[landmark];
  const w = weightKg && weightKg > 0 ? weightKg : spec.scalerMean[2];
  const raw = [ramanujanCm, heightCm, w];
  let pred = spec.intercept;
  for (let i = 0; i < raw.length; i++) {
    const z = (raw[i] - spec.scalerMean[i]) / spec.scalerScale[i];
    pred += spec.coefficients[i] * z;
  }
  return Number(pred.toFixed(2));
}

// 5. Sizing
const UNIQLO_BRACKETS = [
  { size: "XS", chest: [78.0, 84.0], waist: [66.0, 72.0] },
  { size: "S", chest: [84.0, 92.0], waist: [72.0, 80.0] },
  { size: "M", chest: [92.0, 100.0], waist: [80.0, 88.0] },
  { size: "L", chest: [100.0, 108.0], waist: [88.0, 96.0] },
  { size: "XL", chest: [108.0, 116.0], waist: [96.0, 104.0] },
  { size: "XXL", chest: [116.0, 128.0], waist: [104.0, 116.0] },
];
const SIZES = ["XS", "S", "M", "L", "XL", "XXL"];

function recommendSize(chestCm, waistCm) {
  if (!chestCm || chestCm <= 0) return { status: "ABSTAIN_MISSING_INPUT" };
  if (chestCm < 78.0 || chestCm > 128.0) return { status: "ABSTAIN_OUT_OF_BOUNDS" };

  const matchDim = (val, key) => {
    for (const b of UNIQLO_BRACKETS) {
      if (val >= b[key][0] && val < b[key][1]) return b.size;
    }
    if (val === UNIQLO_BRACKETS[UNIQLO_BRACKETS.length - 1][key][1]) return "XXL";
    return null;
  };

  const cSize = matchDim(chestCm, "chest");
  const wSize = waistCm ? matchDim(waistCm, "waist") : null;

  if (cSize && wSize) {
    const cIdx = SIZES.indexOf(cSize);
    const wIdx = SIZES.indexOf(wSize);
    return {
      status: "RECOMMENDED",
      size: wIdx > cIdx ? wSize : cSize,
      accommodating: wIdx > cIdx,
    };
  }
  return { status: "RECOMMENDED", size: cSize, accommodating: false };
}

// 6. End-to-End Pipeline Simulator
function runPipelineSimulator(heightCm, weightKg, frontW, sideD) {
  // Scale calibration
  const scale = calibrateScale(heightCm, 1000, 0.0);
  assert.strictEqual(scale.isValid, true);

  // Cross section widths (px to cm)
  const chestW_cm = frontW * scale.cmPerPixel;
  const chestD_cm = sideD * scale.cmPerPixel;

  // Ramanujan
  const rawCirc = calculateEllipseCircumference(chestW_cm, chestD_cm);

  // Ridge
  const calCirc = calibrateRidge("chest", rawCirc, heightCm, weightKg);

  // Size
  const sizing = recommendSize(calCirc, 82.0);

  return { rawCirc, calCirc, sizing };
}

// RUN TESTS
console.log("=" .repeat(60));
console.log("RUNNING MOBILE REFERENCE ENGINE MATHEMATICAL PARITY CHECKS");
console.log("=" .repeat(60));

// Test 1: Circle
const c1 = calculateEllipseCircumference(20.0, 20.0);
assert.strictEqual(c1, 62.83, "Circle circumference should be 62.83");
console.log("✔ Test 1: Ramanujan circle special case (20x20 cm -> 62.83 cm) PASSED");

// Test 2: Ellipse
const c2 = calculateEllipseCircumference(10.0, 6.0);
assert.strictEqual(c2, 25.53, "Ellipse circumference should be 25.53");
console.log("✔ Test 2: Ramanujan known ellipse (10x6 cm -> 25.53 cm) PASSED");

// Test 3: Scale
const s1 = calibrateScale(175.0, 875, 0.0);
assert.strictEqual(s1.isValid, true);
assert.strictEqual(s1.pixelsPerCm, 5.0);
assert.strictEqual(s1.cmPerPixel, 0.2);
console.log("✔ Test 3: Scale calibration (175 cm / 875 px -> 5.0 px/cm) PASSED");

// Test 4: Pair Scale Consistency
const sFront = calibrateScale(175.0, 875, 0.0);
const sSideGood = calibrateScale(175.0, 860, 0.0);
const sSideBad = calibrateScale(175.0, 750, 0.0);
assert.strictEqual(verifyPairScale(sFront, sSideGood).isValid, true);
assert.strictEqual(verifyPairScale(sFront, sSideBad).isValid, false);
console.log("✔ Test 4: Pair scale consistency (1.7% pass, 15.3% fail) PASSED");

// Test 5: Ridge Regression
const meanC = calibrateRidge("chest", RIDGE_SPECS.chest.scalerMean[0], RIDGE_SPECS.chest.scalerMean[1], RIDGE_SPECS.chest.scalerMean[2]);
assert.strictEqual(meanC, 102.22);
const meanW = calibrateRidge("waist", RIDGE_SPECS.waist.scalerMean[0], RIDGE_SPECS.waist.scalerMean[1], RIDGE_SPECS.waist.scalerMean[2]);
assert.strictEqual(meanW, 91.47);
console.log("✔ Test 5: Phase S1 Ridge Regression at feature means (Chest 102.22 cm, Waist 91.47 cm) PASSED");

// Test 6: Sizing Standard & Ties
assert.strictEqual(recommendSize(95.0, 82.0).size, "M");
assert.strictEqual(recommendSize(92.0).size, "M");
assert.strictEqual(recommendSize(100.0).size, "L");
console.log("✔ Test 6: Uniqlo sizing standard (95cm -> M) and boundary ties (92cm -> M, 100cm -> L) PASSED");

// Test 7: Sizing Accommodating & Abstentions
const accom = recommendSize(90.0, 84.0);
assert.strictEqual(accom.size, "M");
assert.strictEqual(accom.accommodating, true);
assert.strictEqual(recommendSize(70.0).status, "ABSTAIN_OUT_OF_BOUNDS");
assert.strictEqual(recommendSize(null).status, "ABSTAIN_MISSING_INPUT");
console.log("✔ Test 7: Accommodating fit (Chest S, Waist M -> M) and abstentions PASSED");

// Test 8: End-to-End Pipeline Simulator
const pipe = runPipelineSimulator(175.0, 70.0, 180, 130);
assert.strictEqual(pipe.rawCirc > 0, true);
assert.strictEqual(pipe.calCirc > 0, true);
assert.strictEqual(pipe.sizing.status, "RECOMMENDED");
console.log("✔ Test 8: End-to-end measurement & sizing pipeline simulation PASSED");

// Test 9: SMPL-Anthropometry Convex Hull Perimeter & Standard Labels (A–P)
function computeConvexHull2D(points) {
  if (points.length <= 2) return points;
  const sorted = [...points].sort((a, b) => (a.x === b.x ? a.y - b.y : a.x - b.x));
  const cross = (o, a, b) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const lower = [];
  for (const p of sorted) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
      lower.pop();
    }
    lower.push(p);
  }
  const upper = [];
  for (let i = sorted.length - 1; i >= 0; i--) {
    const p = sorted[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) {
      upper.pop();
    }
    upper.push(p);
  }
  lower.pop();
  upper.pop();
  return lower.concat(upper);
}

function computeContourPerimeter(points) {
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

// 20x20 square perimeter = 80 cm
const squarePoints = [
  { x: -10, y: -10 }, { x: 10, y: -10 },
  { x: 10, y: 10 }, { x: -10, y: 10 },
  { x: 0, y: 0 } // interior point
];
const squarePerimeter = computeContourPerimeter(squarePoints);
assert.strictEqual(squarePerimeter, 80.0, "Convex hull perimeter of 20x20 square must be 80.0 cm");

// Height normalization: scale from 180cm to 175cm
const rawHeight = 180.0;
const targetHeight = 175.0;
const rawShoulder = 44.0;
const normalizedShoulder = Number(((rawShoulder / rawHeight) * targetHeight).toFixed(2));
assert.strictEqual(normalizedShoulder, 42.78);
console.log("✔ Test 9: SMPL-Anthropometry convex hull perimeter (80.0 cm) & height normalization PASSED");

console.log("=" .repeat(60));
console.log("ALL 9 PARITY VERIFICATION CHECKS PASSED WITH 100% ACCURACY!");
console.log("=" .repeat(60));
