import React, { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";
import { colors } from "../theme/colors";

interface StabilizationRingProps {
  countdownSeconds: number; // 3, 2, 1, or 0
  isActive: boolean;
  onComplete: () => void;
}

export const StabilizationRing: React.FC<StabilizationRingProps> = ({
  countdownSeconds,
  isActive,
  onComplete,
}) => {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const hasTriggeredRef = useRef<boolean>(false);

  useEffect(() => {
    let anim: Animated.CompositeAnimation | null = null;
    if (isActive) {
      hasTriggeredRef.current = false;
      anim = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.15,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1.0,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      );
      anim.start();
    } else {
      pulseAnim.setValue(1);
    }

    return () => {
      if (anim) {
        anim.stop();
      }
    };
  }, [isActive]);

  useEffect(() => {
    if (isActive && countdownSeconds === 0 && !hasTriggeredRef.current) {
      hasTriggeredRef.current = true;
      onComplete();
    }
  }, [isActive, countdownSeconds, onComplete]);

  if (!isActive) return null;

  return (
    <View style={styles.container} pointerEvents="none">
      <Animated.View
        style={[
          styles.outerRing,
          {
            transform: [{ scale: pulseAnim }],
          },
        ]}
      >
        <View style={styles.innerCircle}>
          <Text style={styles.countdownText}>{countdownSeconds}</Text>
          <Text style={styles.holdText}>HOLD STILL</Text>
        </View>
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: "absolute",
    alignSelf: "center",
    top: "35%",
    zIndex: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  outerRing: {
    width: 110,
    height: 110,
    borderRadius: 55,
    borderWidth: 3,
    borderColor: colors.success,
    backgroundColor: "rgba(16, 185, 129, 0.2)",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: colors.success,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.9,
    shadowRadius: 15,
    elevation: 8,
  },
  innerCircle: {
    alignItems: "center",
    justifyContent: "center",
  },
  countdownText: {
    fontSize: 40,
    fontWeight: "900",
    color: "#FFFFFF",
    lineHeight: 44,
  },
  holdText: {
    fontSize: 9,
    fontWeight: "800",
    color: colors.success,
    letterSpacing: 1,
    marginTop: 2,
  },
});
