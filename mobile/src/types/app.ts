/**
 * Application & Wizard Navigation State Types.
 */

import { FullMeasurementEstimate } from "./index";

export type WizardStep =
  | "DETAILS"
  | "LIVE_CAMERA"
  | "FRONT_CAPTURE"
  | "SIDE_CAPTURE"
  | "PROCESSING"
  | "RESULTS";

export interface UserDetailsState {
  heightCm: number;
  weightKg: number | null;
  heightUnit: "cm" | "in";
  weightUnit: "kg" | "lbs";
  consentGiven: boolean;
  retentionAgreed: boolean;
}

export interface CapturedFrame {
  uri: string;
  width: number;
  height: number;
  timestamp: number;
  view: "front" | "side";
  tiltAngleDegrees: number;
}

export interface SessionData {
  details: UserDetailsState;
  frontFrame: CapturedFrame | null;
  sideFrame: CapturedFrame | null;
  estimate: FullMeasurementEstimate | null;
  manualOverrides: {
    chestCm?: number;
    waistCm?: number;
    hipCm?: number;
  };
}
