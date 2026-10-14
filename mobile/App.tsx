import React, { useState } from "react";
import { SafeAreaView, StatusBar, StyleSheet, View } from "react-native";
import { Header } from "./src/components/Header";
import { DetailsScreen } from "./src/screens/DetailsScreen";
import { FrontCaptureScreen } from "./src/screens/FrontCaptureScreen";
import { LiveCameraScreen } from "./src/screens/LiveCameraScreen";
import { ProcessingScreen } from "./src/screens/ProcessingScreen";
import { ResultsScreen } from "./src/screens/ResultsScreen";
import { SideCaptureScreen } from "./src/screens/SideCaptureScreen";
import { colors } from "./src/theme/colors";
import { FullMeasurementEstimate } from "./src/types";
import { CapturedFrame, SessionData, UserDetailsState, WizardStep } from "./src/types/app";

const INITIAL_DETAILS: UserDetailsState = {
  heightCm: 175.0,
  weightKg: 70.0,
  heightUnit: "cm",
  weightUnit: "kg",
  consentGiven: true,
  retentionAgreed: true,
};

const INITIAL_SESSION: SessionData = {
  details: INITIAL_DETAILS,
  frontFrame: null,
  sideFrame: null,
  estimate: null,
  manualOverrides: {},
};

export default function App() {
  const [currentStep, setCurrentStep] = useState<WizardStep>("DETAILS");
  const [session, setSession] = useState<SessionData>(INITIAL_SESSION);

  // 1. Submit Details -> Start Live Camera Feed & Measurements
  const handleStartLiveCamera = (details: UserDetailsState) => {
    setSession((prev) => ({ ...prev, details }));
    setCurrentStep("LIVE_CAMERA");
  };

  // 2. Submit Details -> Guided 2-Photo Protocol
  const handleDetailsSubmit = (details: UserDetailsState) => {
    setSession((prev) => ({ ...prev, details }));
    setCurrentStep("FRONT_CAPTURE");
  };

  // 3. Live Measurements Locked -> Go directly to Results
  const handleLiveMeasurementsLocked = (estimate: FullMeasurementEstimate) => {
    setSession((prev) => ({ ...prev, estimate }));
    setCurrentStep("RESULTS");
  };

  // 4. Update Height Anchor in live session
  const handleUpdateHeight = (newHeightCm: number) => {
    setSession((prev) => ({
      ...prev,
      details: { ...prev.details, heightCm: newHeightCm },
    }));
  };

  // 5. Capture Front -> go to Side Capture
  const handleFrontCaptured = (frame: CapturedFrame) => {
    setSession((prev) => ({ ...prev, frontFrame: frame }));
    setCurrentStep("SIDE_CAPTURE");
  };

  // 6. Capture Side -> go to Processing
  const handleSideCaptured = (frame: CapturedFrame) => {
    setSession((prev) => ({ ...prev, sideFrame: frame }));
    setCurrentStep("PROCESSING");
  };

  // 7. Processing Success -> go to Results
  const handleProcessingSuccess = (estimate: FullMeasurementEstimate) => {
    setSession((prev) => ({ ...prev, estimate }));
    setCurrentStep("RESULTS");
  };

  // Back Navigation Handler
  const handleBack = () => {
    if (currentStep === "LIVE_CAMERA" || currentStep === "FRONT_CAPTURE") {
      setCurrentStep("DETAILS");
    } else if (currentStep === "SIDE_CAPTURE") {
      setCurrentStep("FRONT_CAPTURE");
    } else if (currentStep === "RESULTS") {
      setCurrentStep("DETAILS");
    }
  };

  // Reset Handler
  const handleReset = () => {
    setSession(INITIAL_SESSION);
    setCurrentStep("DETAILS");
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="light-content" backgroundColor={colors.background} />
      <View style={styles.container}>
        {/* Persistent Header */}
        <Header
          currentStep={currentStep}
          onBack={currentStep !== "DETAILS" && currentStep !== "PROCESSING" ? handleBack : undefined}
          onReset={handleReset}
        />

        {/* Step Views */}
        <View style={styles.stepContainer}>
          {currentStep === "DETAILS" && (
            <DetailsScreen
              initialDetails={session.details}
              onSubmit={handleDetailsSubmit}
              onStartLiveAR={handleStartLiveCamera}
            />
          )}

          {currentStep === "LIVE_CAMERA" && (
            <LiveCameraScreen
              session={session}
              onLockMeasurements={handleLiveMeasurementsLocked}
              onSwitchToGuidedCapture={() => setCurrentStep("FRONT_CAPTURE")}
              onUpdateHeight={handleUpdateHeight}
              onCancel={() => setCurrentStep("DETAILS")}
            />
          )}

          {currentStep === "FRONT_CAPTURE" && (
            <FrontCaptureScreen
              onCapture={handleFrontCaptured}
              onCancel={() => setCurrentStep("DETAILS")}
              onSwitchToLiveAR={() => setCurrentStep("LIVE_CAMERA")}
            />
          )}

          {currentStep === "SIDE_CAPTURE" && (
            <SideCaptureScreen
              onCapture={handleSideCaptured}
              onRetakeFront={() => setCurrentStep("FRONT_CAPTURE")}
            />
          )}

          {currentStep === "PROCESSING" && (
            <ProcessingScreen
              session={session}
              onSuccess={handleProcessingSuccess}
              onRetake={() => setCurrentStep("FRONT_CAPTURE")}
            />
          )}

          {currentStep === "RESULTS" && session.estimate && (
            <ResultsScreen
              session={session}
              onNewScan={() => setCurrentStep("DETAILS")}
              onClearData={handleReset}
            />
          )}
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  stepContainer: {
    flex: 1,
  },
});
