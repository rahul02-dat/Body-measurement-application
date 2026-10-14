import React, { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { PrivacyNoticeModal } from "../components/PrivacyNoticeModal";
import { colors } from "../theme/colors";
import { UserDetailsState } from "../types/app";

interface DetailsScreenProps {
  initialDetails: UserDetailsState;
  onSubmit: (details: UserDetailsState) => void;
  onStartLiveAR?: (details: UserDetailsState) => void;
}

export const DetailsScreen: React.FC<DetailsScreenProps> = ({
  initialDetails,
  onSubmit,
  onStartLiveAR,
}) => {
  const [heightCm, setHeightCm] = useState<string>(
    initialDetails.heightCm > 0 ? initialDetails.heightCm.toString() : "175.0"
  );
  const [weightKg, setWeightKg] = useState<string>(
    initialDetails.weightKg !== null && initialDetails.weightKg !== undefined
      ? initialDetails.weightKg.toString()
      : ""
  );
  const [consentGiven, setConsentGiven] = useState<boolean>(initialDetails.consentGiven);
  const [retentionAgreed, setRetentionAgreed] = useState<boolean>(initialDetails.retentionAgreed);
  const [showPrivacyModal, setShowPrivacyModal] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const validateDetails = (): UserDetailsState | null => {
    const parsedHeight = parseFloat(heightCm);
    const parsedWeight = weightKg.trim() ? parseFloat(weightKg) : null;

    if (isNaN(parsedHeight) || parsedHeight < 100 || parsedHeight > 230) {
      setErrorMessage("Please enter a valid standing height between 100 cm and 230 cm.");
      return null;
    }

    if (parsedWeight !== null && (isNaN(parsedWeight) || parsedWeight < 30 || parsedWeight > 250)) {
      setErrorMessage("Please enter a valid weight between 30 kg and 250 kg (or leave blank).");
      return null;
    }

    if (!consentGiven) {
      setErrorMessage("Informed consent is required to proceed with photo processing.");
      return null;
    }

    setErrorMessage(null);
    return {
      heightCm: parsedHeight,
      weightKg: parsedWeight,
      heightUnit: "cm",
      weightUnit: "kg",
      consentGiven,
      retentionAgreed,
    };
  };

  const handleStartLive = () => {
    const details = validateDetails();
    if (details) {
      if (onStartLiveAR) {
        onStartLiveAR(details);
      } else {
        onSubmit(details);
      }
    }
  };

  const handleStartGuided = () => {
    const details = validateDetails();
    if (details) {
      onSubmit(details);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Hero Section */}
        <View style={styles.heroSection}>
          <Text style={styles.heroTitle}>Physical Scale Anchor</Text>
          <Text style={styles.heroDescription}>
            Two guided photos plus your standing height enable deterministic body dimension estimation and retail sizing.
          </Text>
        </View>

        {/* Inputs Card */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Body Stature Details</Text>

          {/* Height Input */}
          <View style={styles.inputGroup}>
            <View style={styles.inputLabelRow}>
              <Text style={styles.inputLabel}>Standing Height (Barefoot)</Text>
              <Text style={styles.unitBadge}>CENTIMETERS</Text>
            </View>
            <View style={styles.inputWrapper}>
              <TextInput
                style={styles.textInput}
                keyboardType="decimal-pad"
                value={heightCm}
                onChangeText={(t) => {
                  setHeightCm(t);
                  setErrorMessage(null);
                }}
                placeholder="e.g. 175.0"
                placeholderTextColor={colors.textMuted}
              />
              <Text style={styles.inputSuffix}>cm</Text>
            </View>
            <Text style={styles.helperText}>Scale anchor for pixel-to-centimeter conversion</Text>
          </View>

          {/* Weight Input */}
          <View style={styles.inputGroup}>
            <View style={styles.inputLabelRow}>
              <Text style={styles.inputLabel}>Weight (Optional)</Text>
              <Text style={styles.unitBadge}>KILOGRAMS</Text>
            </View>
            <View style={styles.inputWrapper}>
              <TextInput
                style={styles.textInput}
                keyboardType="decimal-pad"
                value={weightKg}
                onChangeText={(t) => {
                  setWeightKg(t);
                  setErrorMessage(null);
                }}
                placeholder="e.g. 70.0"
                placeholderTextColor={colors.textMuted}
              />
              <Text style={styles.inputSuffix}>kg</Text>
            </View>
            <Text style={styles.helperText}>Used for Phase S1 Ridge calibration adjustment</Text>
          </View>
        </View>

        {/* Privacy & Consent Card */}
        <View style={styles.card}>
          <View style={styles.consentHeaderRow}>
            <Text style={styles.cardTitle}>Privacy & Protocol</Text>
            <TouchableOpacity onPress={() => setShowPrivacyModal(true)}>
              <Text style={styles.policyLink}>View Protocol</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.switchRow}>
            <View style={styles.switchTextContainer}>
              <Text style={styles.switchLabel}>Informed Consent</Text>
              <Text style={styles.switchSubLabel}>
                Allow local on-device camera processing to estimate sizing
              </Text>
            </View>
            <Switch
              value={consentGiven}
              onValueChange={(val) => {
                setConsentGiven(val);
                setErrorMessage(null);
              }}
              trackColor={{ false: "#334155", true: colors.primary }}
              thumbColor={consentGiven ? "#FFFFFF" : "#94A3B8"}
            />
          </View>

          <View style={styles.divider} />

          <View style={styles.switchRow}>
            <View style={styles.switchTextContainer}>
              <Text style={styles.switchLabel}>Session Memory Retention</Text>
              <Text style={styles.switchSubLabel}>
                Retain measurements in local cache during active session
              </Text>
            </View>
            <Switch
              value={retentionAgreed}
              onValueChange={setRetentionAgreed}
              trackColor={{ false: "#334155", true: colors.primary }}
              thumbColor={retentionAgreed ? "#FFFFFF" : "#94A3B8"}
            />
          </View>
        </View>

        {errorMessage && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>⚠ {errorMessage}</Text>
          </View>
        )}

        {/* Action Buttons */}
        <TouchableOpacity
          style={[styles.actionButton, !consentGiven && styles.actionButtonDisabled]}
          onPress={handleStartLive}
          activeOpacity={0.8}
        >
          <Text style={styles.actionButtonText}>⚡ Start Live Camera Measurements →</Text>
          <Text style={styles.actionButtonSubtext}>Real-time video feed with live AR calipers & sizing</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.secondaryButton, !consentGiven && styles.actionButtonDisabled]}
          onPress={handleStartGuided}
          activeOpacity={0.8}
        >
          <Text style={styles.secondaryButtonText}>📷 Guided 2-Photo Protocol (Front & Profile)</Text>
        </TouchableOpacity>

        {/* Privacy Notice Modal */}
        <PrivacyNoticeModal visible={showPrivacyModal} onClose={() => setShowPrivacyModal(false)} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  heroSection: {
    marginBottom: 20,
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: "900",
    color: colors.textPrimary,
    letterSpacing: 0.3,
  },
  heroDescription: {
    fontSize: 14,
    color: colors.textSecondary,
    lineHeight: 20,
    marginTop: 6,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: colors.textPrimary,
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabelRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  unitBadge: {
    fontSize: 9,
    fontWeight: "700",
    color: colors.primary,
    letterSpacing: 0.5,
  },
  inputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(15, 23, 42, 0.8)",
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 12,
    paddingHorizontal: 14,
    height: 50,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  inputSuffix: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textMuted,
    marginLeft: 6,
  },
  helperText: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 4,
  },
  consentHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  policyLink: {
    fontSize: 12,
    color: colors.primary,
    fontWeight: "600",
  },
  switchRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 8,
  },
  switchTextContainer: {
    flex: 1,
    paddingRight: 14,
  },
  switchLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  switchSubLabel: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: "rgba(51, 65, 85, 0.3)",
    marginVertical: 8,
  },
  errorBox: {
    backgroundColor: "rgba(239, 68, 68, 0.15)",
    borderWidth: 1,
    borderColor: "rgba(239, 68, 68, 0.4)",
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    color: colors.danger,
    fontSize: 12,
    fontWeight: "600",
  },
  actionButton: {
    backgroundColor: colors.primary,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 8,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  actionButtonDisabled: {
    opacity: 0.5,
  },
  actionButtonText: {
    color: "#04151F",
    fontSize: 16,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  actionButtonSubtext: {
    color: "#0B3C53",
    fontSize: 11,
    fontWeight: "600",
    marginTop: 3,
  },
  secondaryButton: {
    backgroundColor: "rgba(30, 41, 59, 0.6)",
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 10,
    borderWidth: 1,
    borderColor: "rgba(51, 65, 85, 0.6)",
  },
  secondaryButtonText: {
    color: colors.textSecondary,
    fontSize: 14,
    fontWeight: "700",
  },
});
