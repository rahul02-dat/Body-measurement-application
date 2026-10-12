/**
 * TypeScript Data Structures & Interfaces for the Mobile Measurement Engine.
 * Synchronized with Python Reference Engine schemas (schemas.py & measurement_geometry.py).
 */

export interface BodyBounds {
  topY: number;
  bottomY: number;
  spanPixels: number;
  imageHeight: number;
  method: string;
  reliable: boolean;
}

export interface ScaleCalibrationResult {
  pixelsPerCm: number;
  cmPerPixel: number;
  enteredHeightCm: number;
  bodySpanPixels: number;
  bounds: BodyBounds;
  torsoTiltDegrees: number;
  isValid: boolean;
  rejectionReasons: string[];
}

export interface PairScaleResult {
  isValid: boolean;
  discrepancyFraction: number;
  rejectionReasons: string[];
}

export interface CrossSectionSlice {
  name: "chest" | "waist" | "hip";
  frontYPx: number;
  sideYPx: number;
  widthCm: number;
  depthCm: number;
  circumferenceCm: number;
  aspectRatio: number;
  isValid: boolean;
  rejectionReason?: string;
}

export interface CalibratedMeasurement {
  rawRamanujanCm: number;
  calibratedCm: number;
  modelType: string;
  isCalibrated: boolean;
  notes: string;
}

export interface SizeInterval {
  minCm: number;
  maxCm: number;
}

export interface SizeBracket {
  sizeLabel: string;
  chestInterval: SizeInterval;
  waistInterval?: SizeInterval;
}

export interface SizeChart {
  brand: string;
  garmentCategory: string;
  sourceUrl: string;
  retrievalDate: string;
  measurementUnit: string;
  orderedSizes: string[];
  brackets: SizeBracket[];
}

export interface SizeRecommendation {
  recommendedSize: string | null;
  chestSize: string | null;
  waistSize: string | null;
  status: "RECOMMENDED" | "ABSTAIN_OUT_OF_BOUNDS" | "ABSTAIN_MISSING_INPUT";
  abstentionReason?: string;
  notes: string;
}

export interface FullMeasurementEstimate {
  chest: CalibratedMeasurement;
  waist: CalibratedMeasurement;
  hip: CalibratedMeasurement;
  scaleFront: ScaleCalibrationResult;
  scaleSide: ScaleCalibrationResult;
  sizing: SizeRecommendation;
  isValid: boolean;
  rejectionReasons: string[];
}
