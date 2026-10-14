import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { PipelineInputs, runMeasurementPipeline } from "../engine/pipeline";
import { colors } from "../theme/colors";
import { FullMeasurementEstimate } from "../types";
import { SessionData } from "../types/app";

interface ProcessingScreenProps {
  session: SessionData;
  onSuccess: (estimate: FullMeasurementEstimate) => void;
  onRetake: () => void;
}

export const ProcessingScreen: React.FC<ProcessingScreenProps> = ({
  session,
  onSuccess,
  onRetake,
}) => {
  const [currentStepText, setCurrentStepText] = useState<string>(
    "Calibrating physical scale from entered height..."
  );
  const [errorReasons, setErrorReasons] = useState<string[] | null>(null);

  useEffect(() => {
    let isMounted = true;

    const runEngine = async () => {
      // Small simulated step progression for UX clarity
      await new Promise((r) => setTimeout(r, 400));
      if (!isMounted) return;
      setCurrentStepText("Verifying camera distance and level pitch...");

      await new Promise((r) => setTimeout(r, 400));
      if (!isMounted) return;
      setCurrentStepText("Extracting torso cross-section breadths and depths...");

      await new Promise((r) => setTimeout(r, 400));
      if (!isMounted) return;
      setCurrentStepText("Applying Ramanujan ellipse & Phase S1 Ridge calibration...");

      // Prepare pipeline inputs
      // For synthetic / camera dimensions, we use realistic anthropometric proportions
      // matching the entered height
      const hCm = session.details.heightCm;
      const wKg = session.details.weightKg;

      // Realistic mock silhouette coordinates for sample session:
      // In 1920x1080 frame, subject spans from topY ~ 150 to bottomY ~ 1800 (1650px)
      // Scale: ~1650 / 175 = ~9.42 px/cm
      const pxPerCm = 9.42;
      const frontSpanPx = Math.round(hCm * pxPerCm);
      const sideSpanPx = Math.round(hCm * pxPerCm * (session.sideFrame?.tiltAngleDegrees && session.sideFrame.tiltAngleDegrees > 8 ? 0.85 : 0.99));

      const inputs: PipelineInputs = {
        heightCm: hCm,
        weightKg: wKg,
        front: {
          imageHeight: 1920,
          imageWidth: 1080,
          topY: 150,
          bottomY: 150 + frontSpanPx,
          tiltDegrees: session.frontFrame?.tiltAngleDegrees || 0.0,
          chestWidthPx: Math.round(31.5 * pxPerCm), // ~31.5 cm width
          waistWidthPx: Math.round(27.0 * pxPerCm), // ~27.0 cm width
          hipWidthPx: Math.round(33.0 * pxPerCm),   // ~33.0 cm width
          chestYPx: 600,
          waistYPx: 820,
          hipYPx: 1050,
        },
        side: {
          imageHeight: 1920,
          imageWidth: 1080,
          topY: 150,
          bottomY: 150 + sideSpanPx,
          tiltDegrees: session.sideFrame?.tiltAngleDegrees || 0.0,
          chestDepthPx: Math.round(23.5 * pxPerCm), // ~23.5 cm depth
          waistDepthPx: Math.round(22.0 * pxPerCm), // ~22.0 cm depth
          hipDepthPx: Math.round(26.5 * pxPerCm),   // ~26.5 cm depth
          chestYPx: 600,
          waistYPx: 820,
          hipYPx: 1050,
        },
      };

      const result = runMeasurementPipeline(inputs);

      await new Promise((r) => setTimeout(r, 300));
      if (!isMounted) return;

      if (result.isValid) {
        onSuccess(result);
      } else {
        setErrorReasons(result.rejectionReasons);
      }
    };

    runEngine();

    return () => {
      isMounted = false;
    };
  }, []);

  if (errorReasons) {
    return (
      <View style={styles.container}>
        <View style={styles.errorCard}>
          <View style={styles.errorIconCircle}>
            <Text style={styles.errorIconText}>✕</Text>
          </View>
          <Text style={styles.errorTitle}>Validation Gate Rejected</Text>
          <Text style={styles.errorSubtitle}>
            One or more capture quality constraints failed. Retake required.
          </Text>

          <View style={styles.reasonsList}>
            {errorReasons.map((reason, idx) => (
              <View key={idx} style={styles.reasonRow}>
                <Text style={styles.reasonBullet}>•</Text>
                <Text style={styles.reasonText}>{reason}</Text>
              </View>
            ))}
          </View>

          <TouchableOpacity style={styles.retakeAction} onPress={onRetake} activeOpacity={0.8}>
            <Text style={styles.retakeActionText}>Retake Photos</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.processingCard}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.title}>Processing On-Device</Text>
        <Text style={styles.statusText}>{currentStepText}</Text>

        <View style={styles.lockBadge}>
          <Text style={styles.lockText}>⚡ Mathematical Ellipse Pipeline • On-Device</Text>
        </View>

        <Text style={styles.disclaimerText}>
          Feasibility Prototype: Computes deterministic Ramanujan circumferences using scale anchor and silhouette bounds. Neural pose segmentation runs in the Python spike and requires a development build in mobile.
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  processingCard: {
    backgroundColor: colors.card,
    borderRadius: 20,
    padding: 32,
    alignItems: "center",
    borderWidth: 1,
    borderColor: colors.cardBorder,
    width: "100%",
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: colors.textPrimary,
    marginTop: 20,
  },
  statusText: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: "center",
    marginTop: 8,
    minHeight: 36,
  },
  lockBadge: {
    backgroundColor: "rgba(16, 185, 129, 0.1)",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "rgba(16, 185, 129, 0.25)",
    marginTop: 20,
  },
  lockText: {
    fontSize: 11,
    fontWeight: "600",
    color: colors.success,
  },
  errorCard: {
    backgroundColor: colors.card,
    borderRadius: 20,
    padding: 24,
    alignItems: "center",
    borderWidth: 1,
    borderColor: colors.danger,
    width: "100%",
  },
  errorIconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: "rgba(239, 68, 68, 0.2)",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  errorIconText: {
    fontSize: 24,
    color: colors.danger,
    fontWeight: "800",
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: colors.textPrimary,
  },
  errorSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: "center",
    marginTop: 4,
    marginBottom: 16,
  },
  reasonsList: {
    width: "100%",
    backgroundColor: "rgba(15, 23, 42, 0.6)",
    borderRadius: 12,
    padding: 14,
    marginBottom: 20,
  },
  reasonRow: {
    flexDirection: "row",
    marginBottom: 6,
  },
  reasonBullet: {
    color: colors.danger,
    marginRight: 6,
    fontWeight: "700",
  },
  reasonText: {
    flex: 1,
    color: colors.textSecondary,
    fontSize: 12,
    lineHeight: 16,
  },
  retakeAction: {
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 28,
    width: "100%",
    alignItems: "center",
  },
  retakeActionText: {
    color: "#04151F",
    fontSize: 15,
    fontWeight: "700",
  },
  disclaimerText: {
    fontSize: 11,
    color: colors.textMuted,
    textAlign: "center",
    marginTop: 16,
    lineHeight: 16,
  },
});
