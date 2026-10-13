import React, { useEffect, useState } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { LevelIndicator } from "../components/LevelIndicator";
import { SilhouetteOverlay } from "../components/SilhouetteOverlay";
import { StabilizationRing } from "../components/StabilizationRing";
import { colors } from "../theme/colors";
import { CapturedFrame } from "../types/app";

interface FrontCaptureScreenProps {
  onCapture: (frame: CapturedFrame) => void;
  onCancel: () => void;
}

export const FrontCaptureScreen: React.FC<FrontCaptureScreenProps> = ({ onCapture, onCancel }) => {
  const [tiltDegrees, setTiltDegrees] = useState<number>(0.5);
  const [isAligned, setIsAligned] = useState<boolean>(true);
  const [countdownSeconds, setCountdownSeconds] = useState<number>(3);
  const [isCountingDown, setIsCountingDown] = useState<boolean>(false);
  const [instructionText, setInstructionText] = useState<string>(
    "Step back 2.5–3m. Align head & feet with dotted lines. Hold arms away 20°–30°."
  );

  // Auto stabilization countdown trigger
  useEffect(() => {
    let timer: NodeJS.Timeout;

    if (isAligned && Math.abs(tiltDegrees) <= 8.0) {
      setIsCountingDown(true);
      timer = setInterval(() => {
        setCountdownSeconds((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      setIsCountingDown(false);
      setCountdownSeconds(3);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isAligned, tiltDegrees]);

  const handleCaptureComplete = () => {
    const frame: CapturedFrame = {
      uri: "local://front_capture.jpg",
      width: 1080,
      height: 1920,
      timestamp: Date.now(),
      view: "front",
      tiltAngleDegrees: tiltDegrees,
    };
    onCapture(frame);
  };

  return (
    <View style={styles.container}>
      {/* Camera Viewport / Preview Layer */}
      <View style={styles.cameraViewport}>
        <View style={styles.viewfinderBackdrop}>
          <Text style={styles.viewfinderWatermark}>LIVE CAMERA FEED</Text>
        </View>

        {/* Level Indicator (pitch tilt) */}
        <LevelIndicator tiltDegrees={tiltDegrees} />

        {/* Silhouette Overlay */}
        <SilhouetteOverlay
          view="front"
          isAligned={isAligned}
          isTilted={Math.abs(tiltDegrees) > 8.0}
          instructionText={instructionText}
        />

        {/* 3-Second Stance Stabilization Ring */}
        <StabilizationRing
          countdownSeconds={countdownSeconds}
          isActive={isCountingDown}
          onComplete={handleCaptureComplete}
        />
      </View>

      {/* Bottom Controls Bar */}
      <View style={styles.controlsBar}>
        <TouchableOpacity
          style={styles.tiltToggleButton}
          onPress={() => {
            // Toggle tilt to test quality rejection gate
            setTiltDegrees((prev) => (prev === 0.5 ? 9.5 : 0.5));
          }}
          activeOpacity={0.7}
        >
          <Text style={styles.tiltToggleText}>
            Simulate Tilt: {tiltDegrees.toFixed(1)}°
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.shutterButton}
          onPress={handleCaptureComplete}
          activeOpacity={0.8}
        >
          <View style={styles.shutterInner} />
        </TouchableOpacity>

        <TouchableOpacity style={styles.cancelButton} onPress={onCancel} activeOpacity={0.7}>
          <Text style={styles.cancelText}>Cancel</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  cameraViewport: {
    flex: 1,
    position: "relative",
    overflow: "hidden",
  },
  viewfinderBackdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "#0D1322",
    justifyContent: "center",
    alignItems: "center",
  },
  viewfinderWatermark: {
    fontSize: 12,
    fontWeight: "800",
    color: "rgba(51, 65, 85, 0.4)",
    letterSpacing: 2,
  },
  controlsBar: {
    height: 110,
    backgroundColor: "rgba(8, 12, 21, 0.95)",
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 24,
  },
  shutterButton: {
    width: 68,
    height: 68,
    borderRadius: 34,
    borderWidth: 4,
    borderColor: colors.primary,
    backgroundColor: "transparent",
    alignItems: "center",
    justifyContent: "center",
  },
  shutterInner: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: colors.primary,
  },
  tiltToggleButton: {
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: "rgba(30, 41, 59, 0.6)",
    borderWidth: 1,
    borderColor: "rgba(51, 65, 85, 0.4)",
  },
  tiltToggleText: {
    fontSize: 11,
    fontWeight: "600",
    color: colors.textSecondary,
  },
  cancelButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  cancelText: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textMuted,
  },
});
