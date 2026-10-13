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
                <Text style={styles.bold}>100% On-Device Processing:</Text> Your photographs are analyzed locally in volatile memory. No images or biometric records are ever uploaded to cloud servers.
              </Text>
            </View>

            <View style={styles.bulletItem}>
              <Text style={styles.bulletDot}>•</Text>
              <Text style={styles.bulletText}>
                <Text style={styles.bold}>Immediate Data Deletion:</Text> Tapping "Clear & Delete Data" instantly flushes all captured images from your device's memory.
              </Text>
            </View>

            <View style={styles.bulletItem}>
              <Text style={styles.bulletDot}>•</Text>
              <Text style={styles.bulletText}>
                <Text style={styles.bold}>Experimental Prototype:</Text> Measurements are approximations for garment size recommendations. They are not certified for medical, fitness, or bespoke tailoring use.
              </Text>
            </View>

            <View style={styles.bulletItem}>
              <Text style={styles.bulletDot}>•</Text>
              <Text style={styles.bulletText}>
                <Text style={styles.bold}>Informed Consent:</Text> Continued use confirms your voluntary consent to process full-body photographs for clothing size estimation.
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
