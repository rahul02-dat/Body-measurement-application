import React from "react";
import { Modal, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { colors } from "../theme/colors";

interface PrivacyNoticeModalProps {
  visible: boolean;
  onClose: () => void;
}

export const PrivacyNoticeModal: React.FC<PrivacyNoticeModalProps> = ({ visible, onClose }) => {
  return (
    <Modal visible={visible} transparent animationType="fade">
      <View style={styles.scrim}>
        <View style={styles.modalCard}>
          <Text style={styles.modalTitle}>Privacy & Data Protection</Text>
          <Text style={styles.modalSubtitle}>Research-First MVP Protocol</Text>

          <ScrollView style={styles.bodyScroll}>
            <View style={styles.bulletItem}>
              <Text style={styles.bulletDot}>•</Text>
              <Text style={styles.bulletText}>
                <Text style={styles.bold}>No Persistent Storage:</Text> Photos are processed in volatile session memory during the active scan. No images are saved to your photo roll, local disk database, or external servers.
              </Text>
            </View>

            <View style={styles.bulletItem}>
              <Text style={styles.bulletDot}>•</Text>
              <Text style={styles.bulletText}>
                <Text style={styles.bold}>Immediate Session Flush:</Text> Resetting the session or leaving the app immediately clears all in-memory frames and calculated measurements.
              </Text>
            </View>

            <View style={styles.bulletItem}>
              <Text style={styles.bulletDot}>•</Text>
              <Text style={styles.bulletText}>
                <Text style={styles.bold}>Experimental Prototype:</Text> Measurements are approximations for garment size recommendations under study. They are not certified for medical, fitness, or bespoke tailoring use.
              </Text>
            </View>

            <View style={styles.bulletItem}>
              <Text style={styles.bulletDot}>•</Text>
              <Text style={styles.bulletText}>
                <Text style={styles.bold}>Voluntary Informed Consent:</Text> Continued use confirms your voluntary consent to process photos for clothing size estimation.
              </Text>
            </View>
          </ScrollView>

          <TouchableOpacity style={styles.acceptButton} onPress={onClose} activeOpacity={0.8}>
            <Text style={styles.acceptButtonText}>Understood & Agree</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  scrim: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  modalCard: {
    backgroundColor: colors.backgroundSecondary,
    borderRadius: 20,
    padding: 24,
    width: "100%",
    maxHeight: "80%",
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: colors.textPrimary,
  },
  modalSubtitle: {
    fontSize: 12,
    color: colors.textAccent,
    marginTop: 2,
    marginBottom: 16,
  },
  bodyScroll: {
    marginBottom: 20,
  },
  bulletItem: {
    flexDirection: "row",
    marginBottom: 14,
  },
  bulletDot: {
    color: colors.primary,
    fontSize: 18,
    lineHeight: 20,
    marginRight: 10,
  },
  bulletText: {
    flex: 1,
    color: colors.textSecondary,
    fontSize: 13,
    lineHeight: 18,
  },
  bold: {
    fontWeight: "700",
    color: colors.textPrimary,
  },
  acceptButton: {
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  acceptButtonText: {
    color: "#04151F",
    fontSize: 15,
    fontWeight: "700",
  },
});
