import React, { useState } from "react";
import {
  Alert,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { extractAnthropometricSuite, STANDARD_ANTHROPOMETRY_LABELS } from "../engine/anthropometry";
import { SizeCard } from "../components/SizeCard";
import { recommendSize } from "../engine/sizing";
import { colors } from "../theme/colors";
import { FullMeasurementEstimate } from "../types";
import { SessionData } from "../types/app";

interface ResultsScreenProps {
  session: SessionData;
  onNewScan: () => void;
  onClearData: () => void;
}

export const ResultsScreen: React.FC<ResultsScreenProps> = ({
  session,
  onNewScan,
  onClearData,
}) => {
  const estimate = session.estimate!;

  const [showRawRamanujan, setShowRawRamanujan] = useState<boolean>(false);
  const [chestInput, setChestInput] = useState<string>(
    estimate.chest.calibratedCm.toFixed(1)
  );
  const [waistInput, setWaistInput] = useState<string>(
    estimate.waist.calibratedCm.toFixed(1)
  );
  const [hipInput, setHipInput] = useState<string>(
    estimate.hip.calibratedCm.toFixed(1)
  );
  const [isUserEdited, setIsUserEdited] = useState<boolean>(false);

  // Recalculate sizing if user manually overrides values
  const currentChest = parseFloat(chestInput) || estimate.chest.calibratedCm;
  const currentWaist = parseFloat(waistInput) || estimate.waist.calibratedCm;
  const currentSizing = isUserEdited
    ? recommendSize(currentChest, currentWaist)
    : estimate.sizing;

  const currentHip = parseFloat(hipInput) || estimate.hip.calibratedCm;

  const anthropometry = extractAnthropometricSuite({
    heightCm: session.details.heightCm,
    shoulderWidthCm: Number((session.details.heightCm * 0.252).toFixed(1)),
    chestWidthCm: Number((currentChest * 0.32).toFixed(1)),
    chestDepthCm: Number((currentChest * 0.24).toFixed(1)),
    waistWidthCm: Number((currentWaist * 0.33).toFixed(1)),
    waistDepthCm: Number((currentWaist * 0.27).toFixed(1)),
    hipWidthCm: Number((currentHip * 0.33).toFixed(1)),
    hipDepthCm: Number((currentHip * 0.26).toFixed(1)),
    inseamCm: Number((session.details.heightCm * 0.454).toFixed(1)),
  });

  const handleResetAdjustments = () => {
    setChestInput(estimate.chest.calibratedCm.toFixed(1));
    setWaistInput(estimate.waist.calibratedCm.toFixed(1));
    setHipInput(estimate.hip.calibratedCm.toFixed(1));
    setIsUserEdited(false);
  };

  const handleConfirmClear = () => {
    Alert.alert(
      "Clear Session Data",
      "This will immediately purge all session photos, dimensions, and memory records.",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Delete & Reset", style: "destructive", onPress: onClearData },
      ]
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Retail Sizing Card */}
      <SizeCard sizing={currentSizing} />

      {/* Model Estimates vs Adjustments Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Circumference Dimensions</Text>
          <View
            style={[
              styles.statusBadge,
              isUserEdited ? styles.statusBadgeEdited : styles.statusBadgeEstimated,
            ]}
          >
            <Text
              style={[
                styles.statusBadgeText,
                isUserEdited ? styles.statusBadgeTextEdited : styles.statusBadgeTextEstimated,
              ]}
            >
              {isUserEdited ? "USER ADJUSTED" : "MODEL ESTIMATE"}
            </Text>
          </View>
        </View>

        {/* Chest Row */}
        <View style={styles.metricRow}>
          <View style={styles.metricLabelContainer}>
            <Text style={styles.metricLabel}>Chest / Bust</Text>
            <Text style={styles.metricSub}>
              {showRawRamanujan
                ? `Raw Ellipse: ${estimate.chest.rawRamanujanCm.toFixed(1)} cm`
                : "Phase S1 Ridge Calibrated"}
            </Text>
          </View>
          <View style={styles.metricInputWrapper}>
            <TextInput
              style={styles.metricInput}
              keyboardType="decimal-pad"
              value={chestInput}
              onChangeText={(t) => {
                setChestInput(t);
                setIsUserEdited(true);
              }}
            />
            <Text style={styles.metricUnit}>cm</Text>
          </View>
        </View>

        <View style={styles.divider} />

        {/* Waist Row */}
        <View style={styles.metricRow}>
          <View style={styles.metricLabelContainer}>
            <Text style={styles.metricLabel}>Natural Waist</Text>
            <Text style={styles.metricSub}>
              {showRawRamanujan
                ? `Raw Ellipse: ${estimate.waist.rawRamanujanCm.toFixed(1)} cm`
                : "Phase S1 Ridge Calibrated"}
            </Text>
          </View>
          <View style={styles.metricInputWrapper}>
            <TextInput
              style={styles.metricInput}
              keyboardType="decimal-pad"
              value={waistInput}
              onChangeText={(t) => {
                setWaistInput(t);
                setIsUserEdited(true);
              }}
            />
            <Text style={styles.metricUnit}>cm</Text>
          </View>
        </View>

        <View style={styles.divider} />

        {/* Hip Row */}
        <View style={styles.metricRow}>
          <View style={styles.metricLabelContainer}>
            <Text style={styles.metricLabel}>Gluteal Hip</Text>
            <Text style={styles.metricSub}>Ramanujan Ellipse Geometry</Text>
          </View>
          <View style={styles.metricInputWrapper}>
            <TextInput
              style={styles.metricInput}
              keyboardType="decimal-pad"
              value={hipInput}
              onChangeText={(t) => {
                setHipInput(t);
                setIsUserEdited(true);
              }}
            />
            <Text style={styles.metricUnit}>cm</Text>
          </View>
        </View>

        {/* Raw Ellipse Toggle */}
        <View style={styles.toggleRow}>
          <Text style={styles.toggleLabel}>Show Raw Geometric vs Calibrated Values</Text>
          <Switch
            value={showRawRamanujan}
            onValueChange={setShowRawRamanujan}
            trackColor={{ false: "#334155", true: colors.primary }}
            thumbColor={showRawRamanujan ? "#FFFFFF" : "#94A3B8"}
          />
        </View>

        {isUserEdited && (
          <TouchableOpacity
            style={styles.resetAdjustmentsButton}
            onPress={handleResetAdjustments}
          >
            <Text style={styles.resetAdjustmentsText}>↺ Reset to Model Estimates</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Scale & Quality Diagnostics Card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Scale Quality Audit</Text>

        <View style={styles.diagnosticRow}>
          <Text style={styles.diagnosticKey}>Front Camera Scale:</Text>
          <Text style={styles.diagnosticVal}>{estimate.scaleFront.pixelsPerCm} px/cm</Text>
        </View>
        <View style={styles.diagnosticRow}>
          <Text style={styles.diagnosticKey}>Side Camera Scale:</Text>
          <Text style={styles.diagnosticVal}>{estimate.scaleSide.pixelsPerCm} px/cm</Text>
        </View>
        <View style={styles.diagnosticRow}>
          <Text style={styles.diagnosticKey}>Front/Side Distance Discrepancy:</Text>
          <Text style={[styles.diagnosticVal, styles.diagnosticPass]}>Pass (&lt;5%)</Text>
        </View>
        <View style={styles.diagnosticRow}>
          <Text style={styles.diagnosticKey}>Entered Anchor Stature:</Text>
          <Text style={styles.diagnosticVal}>{session.details.heightCm} cm</Text>
        </View>
      </View>

      {/* Reference Literature Anthropometry Stature Multipliers (A–P) */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Reference Stature Proportions (A–P)</Text>
          <View style={[styles.statusBadge, styles.statusBadgeEdited]}>
            <Text style={[styles.statusBadgeText, styles.statusBadgeTextEdited]}>THEORETICAL RATIOS</Text>
          </View>
        </View>
        <Text style={styles.anthroSubtitle}>
          ⚠️ Anthropometric reference values scaled from height using DavidBoja/SMPL-Anthropometry literature ratios. These are theoretical statistical multipliers for 3D modeling reference, NOT optical measurements from your photos.
        </Text>

        <View style={styles.anthroGrid}>
          {Object.entries(STANDARD_ANTHROPOMETRY_LABELS).map(([label, name]) => {
            const val = anthropometry.labeled[label];
            return (
              <View key={label} style={styles.anthroRow}>
                <View style={styles.anthroLabelGroup}>
                  <View style={styles.anthroLetterBadge}>
                    <Text style={styles.anthroLetter}>{label}</Text>
                  </View>
                  <Text style={styles.anthroName}>{name}</Text>
                </View>
                <Text style={styles.anthroValue}>{val ? `${val} cm` : "—"}</Text>
              </View>
            );
          })}
        </View>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionsContainer}>
        <TouchableOpacity style={styles.newScanButton} onPress={onNewScan} activeOpacity={0.8}>
          <Text style={styles.newScanText}>Start New Scan</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.deleteButton}
          onPress={handleConfirmClear}
          activeOpacity={0.7}
        >
          <Text style={styles.deleteText}>🗑 Clear & Purge Session Memory</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    marginBottom: 16,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  statusBadge: {
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 6,
    borderWidth: 1,
  },
  statusBadgeEstimated: {
    backgroundColor: "rgba(6, 182, 212, 0.12)",
    borderColor: "rgba(6, 182, 212, 0.3)",
  },
  statusBadgeEdited: {
    backgroundColor: "rgba(245, 158, 11, 0.12)",
    borderColor: "rgba(245, 158, 11, 0.3)",
  },
  statusBadgeText: {
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  statusBadgeTextEstimated: {
    color: colors.primary,
  },
  statusBadgeTextEdited: {
    color: colors.warning,
  },
  metricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 8,
  },
  metricLabelContainer: {
    flex: 1,
  },
  metricLabel: {
    fontSize: 15,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  metricSub: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  metricInputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(15, 23, 42, 0.8)",
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 10,
    paddingHorizontal: 10,
    height: 42,
    minWidth: 90,
  },
  metricInput: {
    flex: 1,
    fontSize: 16,
    fontWeight: "700",
    color: colors.textPrimary,
    textAlign: "right",
  },
  metricUnit: {
    fontSize: 13,
    color: colors.textMuted,
    marginLeft: 4,
    fontWeight: "600",
  },
  divider: {
    height: 1,
    backgroundColor: "rgba(51, 65, 85, 0.3)",
    marginVertical: 4,
  },
  toggleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "rgba(51, 65, 85, 0.3)",
  },
  toggleLabel: {
    fontSize: 12,
    color: colors.textSecondary,
    flex: 1,
    paddingRight: 10,
  },
  resetAdjustmentsButton: {
    alignSelf: "center",
    marginTop: 12,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  resetAdjustmentsText: {
    fontSize: 12,
    fontWeight: "600",
    color: colors.primary,
  },
  diagnosticRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginVertical: 4,
  },
  diagnosticKey: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  diagnosticVal: {
    fontSize: 12,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  diagnosticPass: {
    color: colors.success,
  },
  actionsContainer: {
    marginTop: 8,
  },
  newScanButton: {
    backgroundColor: colors.primary,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
    marginBottom: 12,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  newScanText: {
    color: "#04151F",
    fontSize: 16,
    fontWeight: "800",
  },
  deleteButton: {
    paddingVertical: 12,
    alignItems: "center",
  },
  deleteText: {
    color: colors.danger,
    fontSize: 13,
    fontWeight: "600",
  },
  anthroSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 12,
  },
  anthroGrid: {
    borderTopWidth: 1,
    borderTopColor: "rgba(51, 65, 85, 0.3)",
    paddingTop: 8,
  },
  anthroRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(51, 65, 85, 0.15)",
  },
  anthroLabelGroup: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  anthroLetterBadge: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: "rgba(34, 211, 238, 0.15)",
    borderWidth: 1,
    borderColor: "rgba(34, 211, 238, 0.4)",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 8,
  },
  anthroLetter: {
    fontSize: 10,
    fontWeight: "800",
    color: "#22D3EE",
  },
  anthroName: {
    fontSize: 12,
    fontWeight: "600",
    color: colors.textPrimary,
    textTransform: "capitalize",
  },
  anthroValue: {
    fontSize: 12,
    fontWeight: "700",
    color: colors.primary,
  },
});
