import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors } from "../theme/colors";

interface SilhouetteOverlayProps {
  view: "front" | "side";
  isAligned: boolean;
  isTilted: boolean;
  instructionText: string;
}

export const SilhouetteOverlay: React.FC<SilhouetteOverlayProps> = ({
  view,
  isAligned,
  isTilted,
  instructionText,
}) => {
  const guideColor = isTilted
    ? colors.danger
    : isAligned
    ? colors.success
    : colors.primary;

  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      {/* Top Head Alignment Line */}
      <View style={styles.topGuideContainer}>
        <View style={[styles.guideLine, { borderColor: guideColor }]} />
        <Text style={[styles.guideLabel, { color: guideColor }]}>TOP OF HEAD (CROWN)</Text>
      </View>

      {/* Main Torso & Body Silhouette Wireframe */}
      <View style={styles.centerContainer}>
        {view === "front" ? (
          <View style={styles.frontWireframeContainer}>
            {/* Head oval */}
            <View style={[styles.headOval, { borderColor: guideColor }]} />
            {/* Neck */}
            <View style={[styles.neck, { borderColor: guideColor }]} />
            {/* Torso */}
            <View style={[styles.frontTorso, { borderColor: guideColor }]}>
              {/* Chest Level */}
              <View style={styles.levelMarker}>
                <View style={[styles.dashedLine, { borderColor: guideColor }]} />
                <Text style={[styles.levelLabel, { color: guideColor }]}>CHEST</Text>
              </View>

              {/* Waist Level */}
              <View style={styles.levelMarker}>
                <View style={[styles.dashedLine, { borderColor: guideColor }]} />
                <Text style={[styles.levelLabel, { color: guideColor }]}>WAIST</Text>
              </View>

              {/* Hip Level */}
              <View style={styles.levelMarker}>
                <View style={[styles.dashedLine, { borderColor: guideColor }]} />
                <Text style={[styles.levelLabel, { color: guideColor }]}>HIP</Text>
              </View>
            </View>

            {/* Arms angle indicator */}
            <View style={styles.armsContainer}>
              <View style={[styles.armLeft, { borderColor: guideColor }]} />
              <View style={[styles.armRight, { borderColor: guideColor }]} />
            </View>

            {/* Legs */}
            <View style={styles.legsContainer}>
              <View style={[styles.leg, { borderColor: guideColor }]} />
              <View style={[styles.leg, { borderColor: guideColor }]} />
            </View>
          </View>
        ) : (
          <View style={styles.sideWireframeContainer}>
            {/* Head profile */}
            <View style={[styles.sideHead, { borderColor: guideColor }]} />
            {/* Side torso silhouette with chest/abdomen profile */}
            <View style={[styles.sideTorso, { borderColor: guideColor }]}>
              <View style={styles.levelMarker}>
                <View style={[styles.dashedLine, { borderColor: guideColor }]} />
                <Text style={[styles.levelLabel, { color: guideColor }]}>BUST DEPTH</Text>
              </View>

              <View style={styles.levelMarker}>
                <View style={[styles.dashedLine, { borderColor: guideColor }]} />
                <Text style={[styles.levelLabel, { color: guideColor }]}>WAIST DEPTH</Text>
              </View>

              <View style={styles.levelMarker}>
                <View style={[styles.dashedLine, { borderColor: guideColor }]} />
                <Text style={[styles.levelLabel, { color: guideColor }]}>GLUTEAL DEPTH</Text>
              </View>
            </View>
            {/* Legs profile */}
            <View style={[styles.sideLeg, { borderColor: guideColor }]} />
          </View>
        )}
      </View>

      {/* Bottom Feet Alignment Line */}
      <View style={styles.bottomGuideContainer}>
        <Text style={[styles.guideLabel, { color: guideColor }]}>FEET ON FLOOR</Text>
        <View style={[styles.guideLine, { borderColor: guideColor }]} />
      </View>

      {/* Instructional HUD Banner */}
      <View style={styles.instructionBanner}>
        <View
          style={[
            styles.instructionCard,
            isTilted && styles.instructionCardDanger,
            isAligned && styles.instructionCardSuccess,
          ]}
        >
          <Text style={styles.instructionText}>{instructionText}</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  topGuideContainer: {
    position: "absolute",
    top: 55,
    left: 20,
    right: 20,
    alignItems: "center",
  },
  bottomGuideContainer: {
    position: "absolute",
    bottom: 90,
    left: 20,
    right: 20,
    alignItems: "center",
  },
  guideLine: {
    width: "100%",
    borderBottomWidth: 2,
    borderStyle: "dashed",
    opacity: 0.8,
  },
  guideLabel: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1,
    marginVertical: 4,
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingTop: 40,
    paddingBottom: 70,
  },
  frontWireframeContainer: {
    alignItems: "center",
    width: 200,
    height: 480,
  },
  headOval: {
    width: 54,
    height: 68,
    borderRadius: 27,
    borderWidth: 2,
    borderStyle: "solid",
    backgroundColor: "rgba(6, 182, 212, 0.05)",
  },
  neck: {
    width: 18,
    height: 14,
    borderLeftWidth: 2,
    borderRightWidth: 2,
  },
  frontTorso: {
    width: 140,
    height: 180,
    borderWidth: 2,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 16,
    justifyContent: "space-around",
    backgroundColor: "rgba(6, 182, 212, 0.04)",
  },
  levelMarker: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 8,
  },
  dashedLine: {
    flex: 1,
    borderBottomWidth: 1,
    borderStyle: "dashed",
    marginRight: 6,
  },
  levelLabel: {
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  armsContainer: {
    position: "absolute",
    top: 90,
    flexDirection: "row",
    width: 220,
    justifyContent: "space-between",
  },
  armLeft: {
    width: 32,
    height: 150,
    borderLeftWidth: 2,
    transform: [{ rotate: "18deg" }],
  },
  armRight: {
    width: 32,
    height: 150,
    borderRightWidth: 2,
    transform: [{ rotate: "-18deg" }],
  },
  legsContainer: {
    flexDirection: "row",
    width: 90,
    justifyContent: "space-between",
    marginTop: 4,
  },
  leg: {
    width: 32,
    height: 200,
    borderLeftWidth: 2,
    borderRightWidth: 2,
    borderBottomWidth: 2,
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
  },
  sideWireframeContainer: {
    alignItems: "center",
    width: 150,
    height: 480,
  },
  sideHead: {
    width: 48,
    height: 68,
    borderRadius: 24,
    borderWidth: 2,
  },
  sideTorso: {
    width: 95,
    height: 180,
    borderWidth: 2,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 24,
    borderBottomLeftRadius: 28,
    borderBottomRightRadius: 14,
    justifyContent: "space-around",
    marginTop: 14,
    backgroundColor: "rgba(6, 182, 212, 0.04)",
  },
  sideLeg: {
    width: 50,
    height: 200,
    borderLeftWidth: 2,
    borderRightWidth: 2,
    borderBottomWidth: 2,
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
    marginTop: 4,
  },
  instructionBanner: {
    position: "absolute",
    bottom: 24,
    left: 20,
    right: 20,
    alignItems: "center",
  },
  instructionCard: {
    backgroundColor: "rgba(15, 23, 42, 0.9)",
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  instructionCardDanger: {
    borderColor: colors.danger,
    backgroundColor: "rgba(239, 68, 68, 0.2)",
  },
  instructionCardSuccess: {
    borderColor: colors.success,
    backgroundColor: "rgba(16, 185, 129, 0.2)",
  },
  instructionText: {
    color: colors.textPrimary,
    fontSize: 13,
    fontWeight: "600",
    textAlign: "center",
  },
});
