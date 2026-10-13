import React, { useState } from "react";
import { SafeAreaView, StatusBar, StyleSheet, View } from "react-native";
import { Header } from "./src/components/Header";
import { DetailsScreen } from "./src/screens/DetailsScreen";
import { FrontCaptureScreen } from "./src/screens/FrontCaptureScreen";
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

  // 1. Submit Details -> go to Front Capture
  const handleDetailsSubmit = (details: UserDetailsState) => {
    setSession((prev) => ({ ...prev, details }));
    setCurrentStep("FRONT_CAPTURE");
  };

  // 2. Capture Front -> go to Side Capture
  const handleFrontCaptured = (frame: CapturedFrame) => {
    setSession((prev) => ({ ...prev, frontFrame: frame }));
    setCurrentStep("SIDE_CAPTURE");
  };

  // 3. Capture Side -> go to Processing
  const handleSideCaptured = (frame: CapturedFrame) => {
    setSession((prev) => ({ ...prev, sideFrame: frame }));
    setCurrentStep("PROCESSING");
  };

  // 4. Processing Success -> go to Results
  const handleProcessingSuccess = (estimate: FullMeasurementEstimate) => {
    setSession((prev) => ({ ...prev, estimate }));
    setCurrentStep("RESULTS");
  };

  // Back Navigation Handler
  const handleBack = () => {
    if (currentStep === "FRONT_CAPTURE") {
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
            />
          )}

          {currentStep === "FRONT_CAPTURE" && (
            <FrontCaptureScreen
              onCapture={handleFrontCaptured}
              onCancel={() => setCurrentStep("DETAILS")}
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
