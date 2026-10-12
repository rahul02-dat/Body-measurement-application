/**
 * Garment Size Chart Recommendation Engine for Mobile App.
 *
 * Implements deterministic size mapping for Uniqlo Adult Tops (XS–XXL).
 * - Exact boundary ties resolve to the larger size (comfort fit preference).
 * - Accommodating fit sizes up when waist dimension requires a larger size.
 * - Out-of-bounds measurements trigger structured abstention.
 *
 * Synchronized with body_measurement.sizing.
 */

import { SizeBracket, SizeChart, SizeRecommendation } from "../types";

export const UNIQLO_ADULT_TOPS_CHART: SizeChart = {
  brand: "Uniqlo",
  garmentCategory: "Adult Tops / T-Shirts",
  sourceUrl: "https://www.uniqlo.com/us/en/size/422992.html",
  retrievalDate: "2026-10-12",
  measurementUnit: "cm",
  orderedSizes: ["XS", "S", "M", "L", "XL", "XXL"],
  brackets: [
    {
      sizeLabel: "XS",
      chestInterval: { minCm: 78.0, maxCm: 84.0 },
      waistInterval: { minCm: 66.0, maxCm: 72.0 },
    },
    {
      sizeLabel: "S",
      chestInterval: { minCm: 84.0, maxCm: 92.0 },
      waistInterval: { minCm: 72.0, maxCm: 80.0 },
    },
    {
      sizeLabel: "M",
      chestInterval: { minCm: 92.0, maxCm: 100.0 },
      waistInterval: { minCm: 80.0, maxCm: 88.0 },
    },
    {
      sizeLabel: "L",
      chestInterval: { minCm: 100.0, maxCm: 108.0 },
      waistInterval: { minCm: 88.0, maxCm: 96.0 },
    },
    {
      sizeLabel: "XL",
      chestInterval: { minCm: 108.0, maxCm: 116.0 },
      waistInterval: { minCm: 96.0, maxCm: 104.0 },
    },
    {
      sizeLabel: "XXL",
      chestInterval: { minCm: 116.0, maxCm: 128.0 },
      waistInterval: { minCm: 104.0, maxCm: 116.0 },
    },
  ],
};

function matchSingleDimension(
  valueCm: number,
  brackets: SizeBracket[],
  dim: "chest" | "waist"
): string | null {
  for (const bracket of brackets) {
    const interval = dim === "chest" ? bracket.chestInterval : bracket.waistInterval;
    if (interval) {
      // Upper boundary preference: [minCm, maxCm)
      if (valueCm >= interval.minCm && valueCm < interval.maxCm) {
        return bracket.sizeLabel;
      }
    }
  }

  // Edge case: maximum boundary of largest bracket
  const largest = brackets[brackets.length - 1];
  const largestInterval = dim === "chest" ? largest.chestInterval : largest.waistInterval;
  if (largestInterval && valueCm === largestInterval.maxCm) {
    return largest.sizeLabel;
  }

  return null;
}

/**
 * Derives deterministic size recommendation from body circumferences.
 *
 * @param chestCm Calibrated chest circumference in cm.
 * @param waistCm Optional calibrated waist circumference in cm.
 * @param chart Target size chart specification (defaults to Uniqlo Adult Tops).
 */
export function recommendSize(
  chestCm: number | null | undefined,
  waistCm?: number | null,
  chart: SizeChart = UNIQLO_ADULT_TOPS_CHART
): SizeRecommendation {
  if (chestCm == null || !Number.isFinite(chestCm) || chestCm <= 0) {
    return {
      recommendedSize: null,
      chestSize: null,
      waistSize: null,
      status: "ABSTAIN_MISSING_INPUT",
      abstentionReason: "Missing or invalid chest measurement.",
      notes: "Please provide a valid positive chest measurement.",
    };
  }

  const minChest = chart.brackets[0].chestInterval.minCm;
  const maxChest = chart.brackets[chart.brackets.length - 1].chestInterval.maxCm;

  if (chestCm < minChest) {
    return {
      recommendedSize: null,
      chestSize: null,
      waistSize: waistCm ? matchSingleDimension(waistCm, chart.brackets, "waist") : null,
      status: "ABSTAIN_OUT_OF_BOUNDS",
      abstentionReason: `Chest (${chestCm.toFixed(1)}cm) is below smallest chart size (<${minChest}cm).`,
      notes: "Measurement is below the minimum covered size bracket.",
    };
  }

  if (chestCm > maxChest) {
    return {
      recommendedSize: null,
      chestSize: null,
      waistSize: waistCm ? matchSingleDimension(waistCm, chart.brackets, "waist") : null,
      status: "ABSTAIN_OUT_OF_BOUNDS",
      abstentionReason: `Chest (${chestCm.toFixed(1)}cm) is above largest chart size (>${maxChest}cm).`,
      notes: "Measurement is above the maximum covered size bracket.",
    };
  }

  const chestSize = matchSingleDimension(chestCm, chart.brackets, "chest");
  const waistSize = waistCm && waistCm > 0 ? matchSingleDimension(waistCm, chart.brackets, "waist") : null;

  if (chestSize && waistSize) {
    const chestIdx = chart.orderedSizes.indexOf(chestSize);
    const waistIdx = chart.orderedSizes.indexOf(waistSize);

    if (waistIdx > chestIdx) {
      return {
        recommendedSize: waistSize,
        chestSize,
        waistSize,
        status: "RECOMMENDED",
        notes: `Accommodating fit: sized up to ${waistSize} for waist (${waistCm!.toFixed(1)}cm).`,
      };
    } else {
      return {
        recommendedSize: chestSize,
        chestSize,
        waistSize,
        status: "RECOMMENDED",
        notes: `Fit driven by chest dimension (${chestCm.toFixed(1)}cm).`,
      };
    }
  }

  return {
    recommendedSize: chestSize,
    chestSize,
    waistSize: null,
    status: "RECOMMENDED",
    notes: "Fit determined by chest dimension alone.",
  };
}

/**
 * Checks whether two size labels are identical or immediately adjacent in the size scale.
 */
export function areAdjacentSizes(
  sizeA: string,
  sizeB: string,
  orderedSizes: string[] = UNIQLO_ADULT_TOPS_CHART.orderedSizes
): boolean {
  const idxA = orderedSizes.indexOf(sizeA);
  const idxB = orderedSizes.indexOf(sizeB);

  if (idxA === -1 || idxB === -1) {
    return false;
  }

  return Math.abs(idxA - idxB) <= 1;
}
