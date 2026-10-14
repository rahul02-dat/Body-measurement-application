import React, { useEffect, useRef, useState } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import { LevelIndicator } from "../components/LevelIndicator";
import { SilhouetteOverlay } from "../components/SilhouetteOverlay";
import { StabilizationRing } from "../components/StabilizationRing";
import { colors } from "../theme/colors";
import { CapturedFrame } from "../types/app";

interface FrontCaptureScreenProps {
  onCapture: (frame: CapturedFrame) => void;
  onCancel: () => void;
  onSwitchToLiveAR?: () => void;
}

export const FrontCaptureScreen: React.FC<FrontCaptureScreenProps> = ({
  onCapture,
  onCancel,
  onSwitchToLiveAR,
}) => {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const [facing, setFacing] = useState<"front" | "back">("back");
  const [tiltDegrees, setTiltDegrees] = useState<number>(0.5);
  const [isAligned, setIsAligned] = useState<boolean>(true);
  const [countdownSeconds, setCountdownSeconds] = useState<number>(3);
  const [isCountingDown, setIsCountingDown] = useState<boolean>(false);
  const [isProcessingCapture, setIsProcessingCapture] = useState<boolean>(false);
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

  const handleCaptureComplete = async () => {
    if (isProcessingCapture) return;
    setIsProcessingCapture(true);
    try {
      let uri = "local://front_capture.jpg";
      let width = 1080;
      let height = 1920;

      if (cameraRef.current && permission?.granted) {
        try {
          const photo = await cameraRef.current.takePictureAsync({
            quality: 0.85,
            skipProcessing: true,
          });
          if (photo?.uri) {
            uri = photo.uri;
            width = photo.width || width;
            height = photo.height || height;
          }
        } catch (e) {
          console.warn("takePictureAsync fallback to mock frame:", e);
        }
      }

      const frame: CapturedFrame = {
        uri,
        width,
        height,
        timestamp: Date.now(),
        view: "front",
        tiltAngleDegrees: tiltDegrees,
      };
      onCapture(frame);
    } finally {
      setIsProcessingCapture(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Top Banner with Flip Camera & Live Mode Switch */}
      <View style={styles.topBar}>
        <TouchableOpacity
          style={styles.pillButton}
          onPress={() => setFacing((prev) => (prev === "back" ? "front" : "back"))}
          activeOpacity={0.7}
        >
          <Text style={styles.pillText}>🔄 {facing === "back" ? "Back" : "Front"}</Text>
        </TouchableOpacity>

        {onSwitchToLiveAR && (
          <TouchableOpacity
            style={[styles.pillButton, styles.livePillButton]}
            onPress={onSwitchToLiveAR}
            activeOpacity={0.7}
          >
            <Text style={styles.livePillText}>⚡ Live AR Measurements</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Camera Viewport / Preview Layer */}
      <View style={styles.cameraViewport}>
        {permission?.granted ? (
          <CameraView
            ref={cameraRef}
            style={StyleSheet.absoluteFill}
            facing={facing}
          />
        ) : (
          <View style={styles.viewfinderBackdrop}>
            <Text style={styles.viewfinderWatermark}>PREVIEW CAMERA ACTIVE</Text>
            <TouchableOpacity style={styles.permBtn} onPress={requestPermission}>
              <Text style={styles.permBtnText}>Grant Camera Permission</Text>
            </TouchableOpacity>
          </View>
        )}

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
  topBar: {
    height: 48,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    backgroundColor: "rgba(8, 12, 21, 0.9)",
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  pillButton: {
    backgroundColor: "rgba(30, 41, 59, 0.8)",
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "rgba(51, 65, 85, 0.5)",
  },
  pillText: {
    fontSize: 11,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  livePillButton: {
    backgroundColor: "rgba(34, 211, 238, 0.15)",
    borderColor: "#22D3EE",
  },
  livePillText: {
    fontSize: 11,
    fontWeight: "800",
    color: "#22D3EE",
  },
  cameraViewport: {
    flex: 1,
    position: "relative",
    overflow: "hidden",
  },
  viewfinderBackdrop: {
    ...StyleSheet.absoluteFill,
    backgroundColor: "#0D1322",
    justifyContent: "center",
    alignItems: "center",
  },
  viewfinderWatermark: {
    fontSize: 12,
    fontWeight: "800",
    color: "rgba(51, 65, 85, 0.6)",
    letterSpacing: 2,
    marginBottom: 10,
  },
  permBtn: {
    backgroundColor: colors.primary,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  permBtnText: {
    color: "#04151F",
    fontSize: 12,
    fontWeight: "800",
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
