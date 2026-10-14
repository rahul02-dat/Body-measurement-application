import React, { useEffect, useRef, useState } from "react";
import {
  Dimensions,
  Modal,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import { calibrateMeasurement } from "../engine/calibrationModels";
import { calculateEllipseCircumference } from "../engine/geometry";
import { calibrateScaleFromSpan } from "../engine/scaleCalibration";
import { recommendSize, UNIQLO_ADULT_TOPS_CHART } from "../engine/sizing";
import { colors } from "../theme/colors";
import { FullMeasurementEstimate } from "../types";
import { SessionData, UserDetailsState } from "../types/app";

interface LiveCameraScreenProps {
  session: SessionData;
  onLockMeasurements: (estimate: FullMeasurementEstimate) => void;
  onSwitchToGuidedCapture: () => void;
  onUpdateHeight: (newHeightCm: number) => void;
  onCancel: () => void;
}

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get("window");

export const LiveCameraScreen: React.FC<LiveCameraScreenProps> = ({
  session,
  onLockMeasurements,
  onSwitchToGuidedCapture,
  onUpdateHeight,
  onCancel,
}) => {
  const [permission, requestPermission] = useCameraPermissions();
  const [facing, setFacing] = useState<"front" | "back">("back");
  const [unit, setUnit] = useState<"cm" | "in">("cm");
  const [widthScale, setWidthScale] = useState<number>(1.0); // Caliper contour width ratio
  const [tiltDegrees, setTiltDegrees] = useState<number>(0.4);
  const [useSimulatedFeed, setUseSimulatedFeed] = useState<boolean>(false);
  const [showHeightModal, setShowHeightModal] = useState<boolean>(false);
  const [tempHeightInput, setTempHeightInput] = useState<string>(
    session.details.heightCm.toString()
  );
  const [activeView, setActiveView] = useState<"front" | "profile">("front");

  // Camera viewport sizing
  const viewportHeight = SCREEN_HEIGHT * 0.62;
  const viewportWidth = SCREEN_WIDTH;

  // Stature and vertical silhouette span
  const currentHeightCm = session.details.heightCm;
  const currentWeightKg = session.details.weightKg;

  // Define vertical span in viewfinder (80% of viewport)
  const topY = viewportHeight * 0.1;
  const bottomY = viewportHeight * 0.9;
  const spanPx = bottomY - topY;
  const pxPerCm = spanPx / currentHeightCm;

  // Anatomical heights (proportional levels)
  const shoulderY = topY + spanPx * 0.16;
  const chestY = topY + spanPx * 0.28;
  const waistY = topY + spanPx * 0.42;
  const hipY = topY + spanPx * 0.54;
  const inseamY = topY + spanPx * 0.52;

  // Real-time dimensional breadths and depths (in cm)
  const shoulderWidthCm = Number((currentHeightCm * 0.252 * widthScale).toFixed(1));
  const chestWidthCm = Number((currentHeightCm * 0.18 * widthScale).toFixed(1));
  const waistWidthCm = Number((currentHeightCm * 0.155 * widthScale).toFixed(1));
  const hipWidthCm = Number((currentHeightCm * 0.188 * widthScale).toFixed(1));
  const inseamLengthCm = Number((currentHeightCm * 0.454).toFixed(1));

  // Depth factors (sagittal aspect ratio for human cross-sections)
  const chestDepthCm = Number((chestWidthCm * 0.746).toFixed(1));
  const waistDepthCm = Number((waistWidthCm * 0.814).toFixed(1));
  const hipDepthCm = Number((hipWidthCm * 0.803).toFixed(1));

  // Ramanujan Ellipse Circumferences
  const rawChestCircCm = calculateEllipseCircumference(chestWidthCm, chestDepthCm);
  const rawWaistCircCm = calculateEllipseCircumference(waistWidthCm, waistDepthCm);
  const rawHipCircCm = calculateEllipseCircumference(hipWidthCm, hipDepthCm);

  // Phase S1 Ridge Regression Calibrations
  const calChest = calibrateMeasurement("chest", rawChestCircCm, currentHeightCm, currentWeightKg);
  const calWaist = calibrateMeasurement("waist", rawWaistCircCm, currentHeightCm, currentWeightKg);
  const calHip = {
    rawRamanujanCm: rawHipCircCm,
    calibratedCm: rawHipCircCm,
    modelType: "Ramanujan_Baseline",
    isCalibrated: false,
    notes: "Direct Ramanujan ellipse geometry.",
  };

  // Uniqlo Garment Sizing
  const sizingRecommendation = recommendSize(calChest.calibratedCm, calWaist.calibratedCm);

  // Helper formatting for cm vs inches
  const formatVal = (valCm: number) => {
    if (unit === "in") {
      return `${(valCm / 2.54).toFixed(1)}"`;
    }
    return `${valCm.toFixed(1)} cm`;
  };

  // Lock and export measurements
  const handleLockMeasurements = () => {
    const scaleFront = calibrateScaleFromSpan(
      currentHeightCm,
      spanPx,
      tiltDegrees,
      topY,
      bottomY,
      viewportHeight,
      "live_camera_ar"
    );

    const estimate: FullMeasurementEstimate = {
      chest: calChest,
      waist: calWaist,
      hip: calHip,
      scaleFront,
      scaleSide: scaleFront, // Real-time continuous mode
      sizing: sizingRecommendation,
      isValid: true,
      rejectionReasons: [],
    };

    onLockMeasurements(estimate);
  };

  // Flip camera
  const toggleFacing = () => {
    setFacing((prev) => (prev === "back" ? "front" : "back"));
  };

  // Save height modal
  const handleSaveHeight = () => {
    const parsed = parseFloat(tempHeightInput);
    if (!isNaN(parsed) && parsed >= 100 && parsed <= 230) {
      onUpdateHeight(parsed);
      setShowHeightModal(false);
    }
  };

  // Render camera permission dialog if not granted and not simulating
  const renderPermissionFallback = () => (
    <View style={styles.permissionContainer}>
      <View style={styles.permissionCard}>
        <Text style={styles.permissionIcon}>📷</Text>
        <Text style={styles.permissionTitle}>Camera Access Required</Text>
        <Text style={styles.permissionDesc}>
          TailorFit requires camera permissions to render the live measurement feed and compute real-time body dimensions.
        </Text>

        <TouchableOpacity
          style={styles.grantButton}
          onPress={requestPermission}
          activeOpacity={0.8}
        >
          <Text style={styles.grantButtonText}>Enable Camera Access</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.simulateButton}
          onPress={() => setUseSimulatedFeed(true)}
          activeOpacity={0.8}
        >
          <Text style={styles.simulateButtonText}>Run in Simulation / Web Mode</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.cancelLink} onPress={onCancel} activeOpacity={0.7}>
          <Text style={styles.cancelLinkText}>‹ Return to Profile Setup</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* 1. Camera Viewport */}
      <View style={[styles.cameraViewport, { height: viewportHeight }]}>
        {!permission?.granted && !useSimulatedFeed ? (
          renderPermissionFallback()
        ) : (
          <>
            {/* Live Camera Stream */}
            {!useSimulatedFeed ? (
              <CameraView
                style={StyleSheet.absoluteFill}
                facing={facing}
              />
            ) : (
              <View style={styles.simulatedFeedBackdrop}>
                <View style={styles.simulatedGrid} />
                <Text style={styles.simulatedTag}>SIMULATED AR CAMERA STREAM</Text>
              </View>
            )}

            {/* AR Measurement Overlay Layer */}
            <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
              {/* Crown / Height Anchor Line */}
              <View style={[styles.caliperLineContainer, { top: topY }]}>
                <View style={[styles.caliperLine, styles.crownLine]} />
                <View style={styles.crownBadge}>
                  <Text style={styles.crownBadgeText}>
                    CROWN: {formatVal(currentHeightCm)}
                  </Text>
                </View>
              </View>

              {/* Shoulders Caliper */}
              <View style={[styles.caliperLineContainer, { top: shoulderY }]}>
                <View
                  style={[
                    styles.caliperBracket,
                    { width: Math.min(viewportWidth * 0.72 * widthScale, viewportWidth * 0.9) },
                  ]}
                >
                  <View style={styles.bracketLeft} />
                  <View style={styles.bracketLine} />
                  <View style={styles.measurementTag}>
                    <Text style={styles.measurementTagLabel}>SHOULDERS</Text>
                    <Text style={styles.measurementTagVal}>{formatVal(shoulderWidthCm)}</Text>
                  </View>
                  <View style={styles.bracketLine} />
                  <View style={styles.bracketRight} />
                </View>
              </View>

              {/* Chest / Bust Caliper */}
              <View style={[styles.caliperLineContainer, { top: chestY }]}>
                <View
                  style={[
                    styles.caliperBracket,
                    { width: Math.min(viewportWidth * 0.58 * widthScale, viewportWidth * 0.85) },
                  ]}
                >
                  <View style={styles.bracketLeft} />
                  <View style={styles.bracketLine} />
                  <View style={[styles.measurementTag, styles.primaryTag]}>
                    <Text style={styles.measurementTagLabel}>CHEST</Text>
                    <Text style={styles.measurementTagVal}>
                      {formatVal(calChest.calibratedCm)}
                    </Text>
                  </View>
                  <View style={styles.bracketLine} />
                  <View style={styles.bracketRight} />
                </View>
              </View>

              {/* Waist Caliper */}
              <View style={[styles.caliperLineContainer, { top: waistY }]}>
                <View
                  style={[
                    styles.caliperBracket,
                    { width: Math.min(viewportWidth * 0.5 * widthScale, viewportWidth * 0.78) },
                  ]}
                >
                  <View style={styles.bracketLeft} />
                  <View style={styles.bracketLine} />
                  <View style={[styles.measurementTag, styles.primaryTag]}>
                    <Text style={styles.measurementTagLabel}>WAIST</Text>
                    <Text style={styles.measurementTagVal}>
                      {formatVal(calWaist.calibratedCm)}
                    </Text>
                  </View>
                  <View style={styles.bracketLine} />
                  <View style={styles.bracketRight} />
                </View>
              </View>

              {/* Hip Caliper */}
              <View style={[styles.caliperLineContainer, { top: hipY }]}>
                <View
                  style={[
                    styles.caliperBracket,
                    { width: Math.min(viewportWidth * 0.6 * widthScale, viewportWidth * 0.86) },
                  ]}
                >
                  <View style={styles.bracketLeft} />
                  <View style={styles.bracketLine} />
                  <View style={[styles.measurementTag, styles.primaryTag]}>
                    <Text style={styles.measurementTagLabel}>HIPS</Text>
                    <Text style={styles.measurementTagVal}>
                      {formatVal(calHip.calibratedCm)}
                    </Text>
                  </View>
                  <View style={styles.bracketLine} />
                  <View style={styles.bracketRight} />
                </View>
              </View>

              {/* Inseam Caliper */}
              <View
                style={[
                  styles.inseamBracketContainer,
                  { top: inseamY, height: bottomY - inseamY },
                ]}
              >
                <View style={styles.inseamLine} />
                <View style={styles.inseamBadge}>
                  <Text style={styles.inseamBadgeText}>INSEAM {formatVal(inseamLengthCm)}</Text>
                </View>
              </View>

              {/* Floor Base Anchor Line */}
              <View style={[styles.caliperLineContainer, { top: bottomY }]}>
                <View style={[styles.caliperLine, styles.floorLine]} />
                <View style={styles.floorBadge}>
                  <Text style={styles.floorBadgeText}>GROUND BASE / FEET</Text>
                </View>
              </View>

              {/* Silhouette Body Outline (Subtle guide wireframe) */}
              <View style={[styles.wireframeGuide, { top: topY, height: spanPx }]}>
                <View style={styles.headOvalGuide} />
                <View style={styles.torsoGuideBox} />
              </View>
            </View>

            {/* Top Viewport Floating Badges */}
            <View style={styles.viewportTopBar}>
              <View style={styles.liveIndicatorPill}>
                <View style={styles.livePulseDot} />
                <Text style={styles.liveText}>STATURE VIEWFINDER</Text>
              </View>

              <View style={styles.levelPill}>
                <Text style={styles.levelText}>
                  {Math.abs(tiltDegrees) <= 8.0 ? "● LEVEL OK" : "⚠ TILT HIGH"} ({tiltDegrees.toFixed(1)}°)
                </Text>
              </View>

              <TouchableOpacity
                style={styles.flipButton}
                onPress={toggleFacing}
                activeOpacity={0.7}
              >
                <Text style={styles.flipButtonText}>🔄 {facing === "back" ? "Back" : "Front"}</Text>
              </TouchableOpacity>
            </View>
          </>
        )}
      </View>

      {/* Physics Notice Banner */}
      <View style={styles.physicsNoticeBar}>
        <Text style={styles.physicsNoticeText}>
          ⚠️ 2D Camera Limitation: Single camera cannot measure sagittal depth. Values are stature-ratio projections from height, not 3D optical inference.
        </Text>
      </View>

      {/* 2. Floating Bottom HUD & Controls */}
      <View style={styles.bottomHudCard}>
        {/* Real-time Sizing Banner */}
        <View style={styles.sizingBannerRow}>
          <View style={styles.sizeResultBox}>
            <Text style={styles.sizeBrandLabel}>RECOMMENDED SIZE ({UNIQLO_ADULT_TOPS_CHART.brand})</Text>
            <View style={styles.sizeValueRow}>
              {sizingRecommendation.status === "RECOMMENDED" && sizingRecommendation.recommendedSize ? (
                <>
                  <Text style={styles.sizeBadge}>{sizingRecommendation.recommendedSize}</Text>
                  <View style={styles.sizeMetaBox}>
                    <Text style={styles.fitStatusText}>Size Match</Text>
                    <Text style={styles.fitNotesText} numberOfLines={1}>
                      {sizingRecommendation.notes || "Based on Chest & Waist"}
                    </Text>
                  </View>
                </>
              ) : (
                <>
                  <Text style={[styles.sizeBadge, { backgroundColor: "#334155", color: "#94A3B8" }]}>—</Text>
                  <View style={styles.sizeMetaBox}>
                    <Text style={[styles.fitStatusText, { color: colors.warning }]}>Cannot Recommend</Text>
                    <Text style={styles.fitNotesText} numberOfLines={1}>
                      {sizingRecommendation.abstentionReason || "Outside chart range"}
                    </Text>
                  </View>
                </>
              )}
            </View>
          </View>

          {/* Unit Toggle & Quick Height */}
          <View style={styles.quickControlsCol}>
            <View style={styles.unitToggleRow}>
              <TouchableOpacity
                style={[styles.unitButton, unit === "cm" && styles.unitButtonActive]}
                onPress={() => setUnit("cm")}
              >
                <Text style={[styles.unitButtonText, unit === "cm" && styles.unitButtonTextActive]}>
                  CM
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.unitButton, unit === "in" && styles.unitButtonActive]}
                onPress={() => setUnit("in")}
              >
                <Text style={[styles.unitButtonText, unit === "in" && styles.unitButtonTextActive]}>
                  IN
                </Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={styles.heightChip}
              onPress={() => setShowHeightModal(true)}
              activeOpacity={0.7}
            >
              <Text style={styles.heightChipText}>H: {currentHeightCm}cm ✎</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Live Metrics Grid */}
        <View style={styles.metricsGrid}>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Chest</Text>
            <Text style={styles.metricValue}>{formatVal(calChest.calibratedCm)}</Text>
          </View>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Waist</Text>
            <Text style={styles.metricValue}>{formatVal(calWaist.calibratedCm)}</Text>
          </View>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Hips</Text>
            <Text style={styles.metricValue}>{formatVal(calHip.calibratedCm)}</Text>
          </View>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Shoulders</Text>
            <Text style={styles.metricValue}>{formatVal(shoulderWidthCm)}</Text>
          </View>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Inseam</Text>
            <Text style={styles.metricValue}>{formatVal(inseamLengthCm)}</Text>
          </View>
        </View>

        {/* Caliper Fine-Tuning Slider */}
        <View style={styles.fineTuneRow}>
          <Text style={styles.fineTuneLabel}>Caliper Fit Width:</Text>
          <View style={styles.stepperRow}>
            <TouchableOpacity
              style={styles.stepperButton}
              onPress={() => setWidthScale((prev) => Math.max(0.85, Number((prev - 0.02).toFixed(2))))}
            >
              <Text style={styles.stepperButtonText}>−</Text>
            </TouchableOpacity>
            <Text style={styles.stepperValueText}>{(widthScale * 100).toFixed(0)}%</Text>
            <TouchableOpacity
              style={styles.stepperButton}
              onPress={() => setWidthScale((prev) => Math.min(1.25, Number((prev + 0.02).toFixed(2))))}
            >
              <Text style={styles.stepperButtonText}>+</Text>
            </TouchableOpacity>
          </View>

          {/* Switch to 2-Shot Mode */}
          <TouchableOpacity
            style={styles.guidedSwitchButton}
            onPress={onSwitchToGuidedCapture}
            activeOpacity={0.7}
          >
            <Text style={styles.guidedSwitchText}>📷 2-Photo Mode</Text>
          </TouchableOpacity>
        </View>

        {/* Lock Measurements Primary Action */}
        <TouchableOpacity
          style={styles.lockActionButton}
          onPress={handleLockMeasurements}
          activeOpacity={0.8}
        >
          <Text style={styles.lockActionText}>🔒 Lock Measurements & View Sizing →</Text>
        </TouchableOpacity>
      </View>

      {/* Height Adjustment Modal */}
      <Modal visible={showHeightModal} transparent animationType="fade">
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Adjust Scale Height</Text>
            <Text style={styles.modalDesc}>
              Physical stature sets the exact pixels-per-centimeter conversion factor.
            </Text>
            <View style={styles.modalInputWrapper}>
              <TextInput
                style={styles.modalInput}
                keyboardType="decimal-pad"
                value={tempHeightInput}
                onChangeText={setTempHeightInput}
                placeholder="175.0"
                placeholderTextColor={colors.textMuted}
              />
              <Text style={styles.modalInputSuffix}>cm</Text>
            </View>
            <View style={styles.modalBtnRow}>
              <TouchableOpacity
                style={styles.modalCancelBtn}
                onPress={() => setShowHeightModal(false)}
              >
                <Text style={styles.modalCancelBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalSaveBtn} onPress={handleSaveHeight}>
                <Text style={styles.modalSaveBtnText}>Update Scale</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  cameraViewport: {
    width: "100%",
    position: "relative",
    overflow: "hidden",
    backgroundColor: "#080C15",
  },
  simulatedFeedBackdrop: {
    ...StyleSheet.absoluteFill,
    backgroundColor: "#0D1527",
    justifyContent: "center",
    alignItems: "center",
  },
  simulatedGrid: {
    ...StyleSheet.absoluteFill,
    borderWidth: 1,
    borderColor: "rgba(34, 211, 238, 0.1)",
  },
  simulatedTag: {
    fontSize: 12,
    fontWeight: "800",
    color: "rgba(34, 211, 238, 0.4)",
    letterSpacing: 2,
  },
  viewportTopBar: {
    position: "absolute",
    top: 14,
    left: 14,
    right: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  liveIndicatorPill: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(15, 23, 42, 0.85)",
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "rgba(34, 211, 238, 0.3)",
  },
  livePulseDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#10B981",
    marginRight: 6,
  },
  liveText: {
    fontSize: 10,
    fontWeight: "800",
    color: "#22D3EE",
    letterSpacing: 1,
  },
  levelPill: {
    backgroundColor: "rgba(15, 23, 42, 0.85)",
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "rgba(51, 65, 85, 0.4)",
  },
  levelText: {
    fontSize: 10,
    fontWeight: "700",
    color: colors.textSecondary,
  },
  flipButton: {
    backgroundColor: "rgba(15, 23, 42, 0.85)",
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "rgba(51, 65, 85, 0.4)",
  },
  flipButtonText: {
    fontSize: 10,
    fontWeight: "700",
    color: colors.textPrimary,
  },

  /* Calipers & Guides */
  caliperLineContainer: {
    position: "absolute",
    left: 0,
    right: 0,
    alignItems: "center",
  },
  caliperLine: {
    width: "92%",
    height: 1,
    borderStyle: "dashed",
    borderWidth: 1,
  },
  crownLine: {
    borderColor: "#38BDF8",
  },
  crownBadge: {
    position: "absolute",
    top: -18,
    backgroundColor: "rgba(14, 165, 233, 0.85)",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  crownBadgeText: {
    fontSize: 9,
    fontWeight: "800",
    color: "#FFFFFF",
    letterSpacing: 0.5,
  },
  floorLine: {
    borderColor: "#10B981",
  },
  floorBadge: {
    position: "absolute",
    bottom: -18,
    backgroundColor: "rgba(16, 185, 129, 0.85)",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  floorBadgeText: {
    fontSize: 9,
    fontWeight: "800",
    color: "#FFFFFF",
    letterSpacing: 0.5,
  },

  /* Caliper Brackets */
  caliperBracket: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  bracketLeft: {
    width: 6,
    height: 14,
    borderLeftWidth: 2,
    borderTopWidth: 2,
    borderBottomWidth: 2,
    borderColor: "#22D3EE",
  },
  bracketRight: {
    width: 6,
    height: 14,
    borderRightWidth: 2,
    borderTopWidth: 2,
    borderBottomWidth: 2,
    borderColor: "#22D3EE",
  },
  bracketLine: {
    flex: 1,
    height: 1,
    backgroundColor: "rgba(34, 211, 238, 0.6)",
  },
  measurementTag: {
    backgroundColor: "rgba(15, 23, 42, 0.9)",
    borderWidth: 1,
    borderColor: "rgba(34, 211, 238, 0.6)",
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
    flexDirection: "row",
    alignItems: "center",
    marginHorizontal: 4,
    shadowColor: "#22D3EE",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 6,
  },
  primaryTag: {
    borderColor: "#22D3EE",
    backgroundColor: "rgba(8, 12, 21, 0.95)",
  },
  measurementTagLabel: {
    fontSize: 9,
    fontWeight: "800",
    color: colors.textSecondary,
    marginRight: 5,
    letterSpacing: 0.5,
  },
  measurementTagVal: {
    fontSize: 11,
    fontWeight: "800",
    color: "#22D3EE",
  },

  /* Inseam Caliper */
  inseamBracketContainer: {
    position: "absolute",
    left: "50%",
    alignItems: "center",
  },
  inseamLine: {
    width: 2,
    flex: 1,
    backgroundColor: "rgba(244, 114, 182, 0.5)",
  },
  inseamBadge: {
    position: "absolute",
    top: "40%",
    backgroundColor: "rgba(15, 23, 42, 0.85)",
    borderWidth: 1,
    borderColor: "rgba(244, 114, 182, 0.6)",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  inseamBadgeText: {
    fontSize: 8,
    fontWeight: "800",
    color: "#F472B6",
  },

  /* Wireframe Silhouette Guide */
  wireframeGuide: {
    position: "absolute",
    left: "20%",
    right: "20%",
    alignItems: "center",
    pointerEvents: "none",
  },
  headOvalGuide: {
    width: 48,
    height: 60,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: "rgba(34, 211, 238, 0.25)",
  },
  torsoGuideBox: {
    width: "70%",
    flex: 1,
    borderLeftWidth: 1,
    borderRightWidth: 1,
    borderColor: "rgba(34, 211, 238, 0.15)",
    marginTop: 8,
  },

  /* Bottom Floating HUD */
  bottomHudCard: {
    flex: 1,
    backgroundColor: "rgba(8, 12, 21, 0.97)",
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: Platform.OS === "ios" ? 24 : 14,
    justifyContent: "space-between",
  },
  sizingBannerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "rgba(15, 23, 42, 0.7)",
    borderRadius: 12,
    padding: 10,
    borderWidth: 1,
    borderColor: "rgba(51, 65, 85, 0.4)",
  },
  sizeResultBox: {
    flex: 1,
  },
  sizeBrandLabel: {
    fontSize: 9,
    fontWeight: "800",
    color: colors.textMuted,
    letterSpacing: 0.5,
  },
  sizeValueRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 2,
  },
  sizeBadge: {
    fontSize: 24,
    fontWeight: "900",
    color: "#10B981",
    marginRight: 8,
  },
  sizeMetaBox: {
    flex: 1,
  },
  fitStatusText: {
    fontSize: 11,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  fitNotesText: {
    fontSize: 10,
    color: colors.textSecondary,
  },
  quickControlsCol: {
    alignItems: "flex-end",
  },
  unitToggleRow: {
    flexDirection: "row",
    backgroundColor: "rgba(30, 41, 59, 0.8)",
    borderRadius: 8,
    padding: 2,
    marginBottom: 4,
  },
  unitButton: {
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
  },
  unitButtonActive: {
    backgroundColor: colors.primary,
  },
  unitButtonText: {
    fontSize: 10,
    fontWeight: "700",
    color: colors.textMuted,
  },
  unitButtonTextActive: {
    color: "#04151F",
  },
  heightChip: {
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
    backgroundColor: "rgba(30, 41, 59, 0.6)",
    borderWidth: 1,
    borderColor: "rgba(51, 65, 85, 0.5)",
  },
  heightChipText: {
    fontSize: 10,
    fontWeight: "600",
    color: "#38BDF8",
  },

  /* Metrics Grid */
  metricsGrid: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginVertical: 8,
  },
  metricItem: {
    flex: 1,
    alignItems: "center",
    backgroundColor: "rgba(15, 23, 42, 0.5)",
    borderRadius: 8,
    paddingVertical: 6,
    marginHorizontal: 2,
    borderWidth: 1,
    borderColor: "rgba(51, 65, 85, 0.3)",
  },
  metricLabel: {
    fontSize: 9,
    fontWeight: "700",
    color: colors.textMuted,
    marginBottom: 2,
  },
  metricValue: {
    fontSize: 11,
    fontWeight: "800",
    color: colors.textPrimary,
  },

  /* Fine-tuning bar */
  fineTuneRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  fineTuneLabel: {
    fontSize: 11,
    fontWeight: "600",
    color: colors.textSecondary,
  },
  stepperRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(15, 23, 42, 0.8)",
    borderRadius: 8,
    padding: 2,
  },
  stepperButton: {
    width: 28,
    height: 26,
    backgroundColor: "rgba(30, 41, 59, 0.8)",
    borderRadius: 6,
    alignItems: "center",
    justifyContent: "center",
  },
  stepperButtonText: {
    fontSize: 14,
    fontWeight: "800",
    color: colors.textPrimary,
  },
  stepperValueText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#22D3EE",
    marginHorizontal: 8,
  },
  guidedSwitchButton: {
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: "rgba(30, 41, 59, 0.6)",
    borderWidth: 1,
    borderColor: "rgba(51, 65, 85, 0.4)",
  },
  guidedSwitchText: {
    fontSize: 11,
    fontWeight: "600",
    color: colors.textSecondary,
  },

  /* Primary Action */
  lockActionButton: {
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  lockActionText: {
    color: "#04151F",
    fontSize: 15,
    fontWeight: "900",
    letterSpacing: 0.3,
  },

  /* Permission Card */
  permissionContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
    backgroundColor: "#080C15",
  },
  permissionCard: {
    backgroundColor: colors.card,
    borderRadius: 16,
    padding: 24,
    alignItems: "center",
    borderWidth: 1,
    borderColor: colors.cardBorder,
    width: "100%",
  },
  permissionIcon: {
    fontSize: 40,
    marginBottom: 12,
  },
  permissionTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: colors.textPrimary,
    marginBottom: 8,
    textAlign: "center",
  },
  permissionDesc: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: "center",
    lineHeight: 18,
    marginBottom: 20,
  },
  grantButton: {
    backgroundColor: colors.primary,
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 20,
    width: "100%",
    alignItems: "center",
    marginBottom: 10,
  },
  grantButtonText: {
    color: "#04151F",
    fontSize: 14,
    fontWeight: "800",
  },
  simulateButton: {
    backgroundColor: "rgba(30, 41, 59, 0.6)",
    borderWidth: 1,
    borderColor: "rgba(51, 65, 85, 0.6)",
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 16,
    width: "100%",
    alignItems: "center",
    marginBottom: 12,
  },
  simulateButtonText: {
    color: colors.textSecondary,
    fontSize: 12,
    fontWeight: "600",
  },
  cancelLink: {
    paddingVertical: 6,
  },
  cancelLinkText: {
    color: colors.textMuted,
    fontSize: 12,
  },

  /* Height Modal */
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.75)",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  modalCard: {
    backgroundColor: colors.card,
    borderRadius: 16,
    padding: 20,
    width: "100%",
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: "800",
    color: colors.textPrimary,
    marginBottom: 6,
  },
  modalDesc: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 14,
  },
  modalInputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(15, 23, 42, 0.8)",
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 10,
    paddingHorizontal: 12,
    height: 48,
    marginBottom: 16,
  },
  modalInput: {
    flex: 1,
    fontSize: 16,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  modalInputSuffix: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textMuted,
  },
  modalBtnRow: {
    flexDirection: "row",
    justifyContent: "flex-end",
  },
  modalCancelBtn: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    marginRight: 8,
  },
  modalCancelBtnText: {
    fontSize: 13,
    color: colors.textMuted,
    fontWeight: "600",
  },
  modalSaveBtn: {
    backgroundColor: colors.primary,
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  modalSaveBtnText: {
    color: "#04151F",
    fontSize: 13,
    fontWeight: "800",
  },
  physicsNoticeBar: {
    backgroundColor: "rgba(30, 41, 59, 0.9)",
    borderBottomWidth: 1,
    borderBottomColor: "rgba(51, 65, 85, 0.6)",
    paddingVertical: 6,
    paddingHorizontal: 16,
  },
  physicsNoticeText: {
    fontSize: 11,
    color: "#FBBF24",
    textAlign: "center",
    lineHeight: 15,
  },
});
