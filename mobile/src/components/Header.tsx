import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { colors } from "../theme/colors";
import { WizardStep } from "../types/app";

interface HeaderProps {
  currentStep: WizardStep;
  onBack?: () => void;
  onReset?: () => void;
}

const STEPS: { key: WizardStep; label: string; number: number }[] = [
  { key: "DETAILS", label: "Details", number: 1 },
  { key: "FRONT_CAPTURE", label: "Front", number: 2 },
  { key: "SIDE_CAPTURE", label: "Side View", number: 3 },
  { key: "RESULTS", label: "Sizing", number: 4 },
];

export const Header: React.FC<HeaderProps> = ({ currentStep, onBack, onReset }) => {
  const isLiveCamera = currentStep === "LIVE_CAMERA";
  const currentStepIndex = isLiveCamera ? 1 : STEPS.findIndex((s) => s.key === currentStep);

  return (
    <View style={styles.container}>
      <View style={styles.topRow}>
        <View style={styles.left}>
          {onBack && currentStep !== "DETAILS" && currentStep !== "RESULTS" ? (
            <TouchableOpacity onPress={onBack} style={styles.backButton} activeOpacity={0.7}>
              <Text style={styles.backText}>‹ Back</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.brandBadge}>
              <Text style={styles.brandBadgeText}>{isLiveCamera ? "LIVE AR" : "MVP SPIKE"}</Text>
            </View>
          )}
        </View>

        <Text style={styles.title}>TailorFit</Text>

        <View style={styles.right}>
          {onReset && (
            <TouchableOpacity onPress={onReset} style={styles.resetButton} activeOpacity={0.7}>
              <Text style={styles.resetText}>Reset</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Step Progress Indicators */}
      <View style={styles.progressRow}>
        {STEPS.map((step, idx) => {
          const isActive = step.key === currentStep || (isLiveCamera && step.key === "FRONT_CAPTURE");
          const isCompleted = currentStepIndex > idx;
          const label = isLiveCamera && step.key === "FRONT_CAPTURE" ? "Live AR" : step.label;

          return (
            <React.Fragment key={step.key}>
              <View style={styles.stepItem}>
                <View
                  style={[
                    styles.stepBadge,
                    isActive && styles.stepBadgeActive,
                    isCompleted && styles.stepBadgeCompleted,
                  ]}
                >
                  <Text
                    style={[
                      styles.stepNumber,
                      isActive && styles.stepNumberActive,
                      isCompleted && styles.stepNumberCompleted,
                    ]}
                  >
                    {isCompleted ? "✓" : step.number}
                  </Text>
                </View>
                <Text
                  style={[
                    styles.stepLabel,
                    isActive && styles.stepLabelActive,
                    isCompleted && styles.stepLabelCompleted,
                  ]}
                >
                  {label}
                </Text>
              </View>

              {idx < STEPS.length - 1 && (
                <View
                  style={[
                    styles.connector,
                    currentStepIndex > idx && styles.connectorCompleted,
                  ]}
                />
              )}
            </React.Fragment>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.background,
    paddingTop: 12,
    paddingBottom: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  topRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 14,
  },
  left: {
    minWidth: 70,
  },
  right: {
    minWidth: 70,
    alignItems: "flex-end",
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: colors.textPrimary,
    letterSpacing: 0.5,
  },
  brandBadge: {
    backgroundColor: "rgba(6, 182, 212, 0.15)",
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "rgba(6, 182, 212, 0.3)",
    alignSelf: "flex-start",
  },
  brandBadgeText: {
    color: colors.primary,
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  backButton: {
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  backText: {
    color: colors.primary,
    fontSize: 15,
    fontWeight: "600",
  },
  resetButton: {
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  resetText: {
    color: colors.textMuted,
    fontSize: 14,
    fontWeight: "500",
  },
  progressRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
  },
  stepItem: {
    alignItems: "center",
  },
  stepBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: "rgba(51, 65, 85, 0.4)",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 4,
  },
  stepBadgeActive: {
    backgroundColor: colors.primary,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 6,
    elevation: 4,
  },
  stepBadgeCompleted: {
    backgroundColor: colors.success,
  },
  stepNumber: {
    fontSize: 11,
    fontWeight: "700",
    color: colors.textMuted,
  },
  stepNumberActive: {
    color: "#04151F",
  },
  stepNumberCompleted: {
    color: "#FFFFFF",
  },
  stepLabel: {
    fontSize: 11,
    color: colors.textMuted,
    fontWeight: "500",
  },
  stepLabelActive: {
    color: colors.primary,
    fontWeight: "700",
  },
  stepLabelCompleted: {
    color: colors.textSecondary,
  },
  connector: {
    width: 28,
    height: 2,
    backgroundColor: "rgba(51, 65, 85, 0.4)",
    marginHorizontal: 6,
    marginBottom: 14,
  },
  connectorCompleted: {
    backgroundColor: colors.success,
  },
});
