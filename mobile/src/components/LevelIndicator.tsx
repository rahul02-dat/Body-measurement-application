import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors } from "../theme/colors";

interface LevelIndicatorProps {
  tiltDegrees: number;
}

export const LevelIndicator: React.FC<LevelIndicatorProps> = ({ tiltDegrees }) => {
  const isLevel = Math.abs(tiltDegrees) <= 8.0;

  return (
    <View style={styles.container}>
      <View
        style={[
          styles.badge,
          isLevel ? styles.badgeLevel : styles.badgeTilted,
        ]}
      >
        <View
          style={[
            styles.dot,
            isLevel ? styles.dotLevel : styles.dotTilted,
          ]}
        />
        <Text
          style={[
            styles.text,
            isLevel ? styles.textLevel : styles.textTilted,
          ]}
        >
          {isLevel
            ? `LEVEL: ${Math.abs(tiltDegrees).toFixed(1)}° (OK)`
            : `TILT: ${Math.abs(tiltDegrees).toFixed(1)}° (KEEP PHONE VERTICAL)`}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: "absolute",
    top: 16,
    alignSelf: "center",
    zIndex: 10,
  },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
    borderWidth: 1,
  },
  badgeLevel: {
    backgroundColor: "rgba(16, 185, 129, 0.15)",
    borderColor: "rgba(16, 185, 129, 0.4)",
  },
  badgeTilted: {
    backgroundColor: "rgba(239, 68, 68, 0.25)",
    borderColor: "rgba(239, 68, 68, 0.6)",
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  dotLevel: {
    backgroundColor: colors.success,
  },
  dotTilted: {
    backgroundColor: colors.danger,
  },
  text: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  textLevel: {
    color: colors.success,
  },
  textTilted: {
    color: colors.danger,
  },
});
