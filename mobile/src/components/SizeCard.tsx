import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { UNIQLO_ADULT_TOPS_CHART } from "../engine/sizing";
import { colors } from "../theme/colors";
import { SizeRecommendation } from "../types";

interface SizeCardProps {
  sizing: SizeRecommendation;
}

export const SizeCard: React.FC<SizeCardProps> = ({ sizing }) => {
  const isRecommended = sizing.status === "RECOMMENDED" && sizing.recommendedSize;

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View>
          <Text style={styles.categoryTitle}>{UNIQLO_ADULT_TOPS_CHART.garmentCategory}</Text>
          <Text style={styles.brandSubtitle}>Brand: {UNIQLO_ADULT_TOPS_CHART.brand}</Text>
        </View>

        <View style={styles.chartTag}>
          <Text style={styles.chartTagText}>OFFICIAL CHART</Text>
        </View>
      </View>

      {/* Main Recommended Size Badge */}
      <View style={styles.badgeSection}>
        {isRecommended ? (
          <View style={styles.sizeBadge}>
            <Text style={styles.sizeLabelPrefix}>RECOMMENDED SIZE</Text>
            <Text style={styles.sizeValue}>{sizing.recommendedSize}</Text>
            <Text style={styles.notesText}>{sizing.notes}</Text>
          </View>
        ) : (
          <View style={[styles.sizeBadge, styles.sizeBadgeAbstain]}>
            <Text style={styles.abstainTitle}>CANNOT RECOMMEND SIZE</Text>
            <Text style={styles.abstainReason}>
              {sizing.abstentionReason || "Measurements outside chart range."}
            </Text>
          </View>
        )}
      </View>

      {/* Uniqlo Size Brackets Spectrum */}
      <View style={styles.spectrumContainer}>
        <Text style={styles.spectrumTitle}>Uniqlo Size Range:</Text>
        <View style={styles.bracketsRow}>
          {UNIQLO_ADULT_TOPS_CHART.orderedSizes.map((sz) => {
            const isMatch = sz === sizing.recommendedSize;
            const bracket = UNIQLO_ADULT_TOPS_CHART.brackets.find((b) => b.sizeLabel === sz);

            return (
              <View
                key={sz}
                style={[
                  styles.bracketPill,
                  isMatch && styles.bracketPillActive,
                ]}
              >
                <Text
                  style={[
                    styles.bracketSizeLabel,
                    isMatch && styles.bracketSizeLabelActive,
                  ]}
                >
                  {sz}
                </Text>
                {bracket && (
                  <Text
                    style={[
                      styles.bracketRangeText,
                      isMatch && styles.bracketRangeTextActive,
                    ]}
                  >
                    {bracket.chestInterval.minCm}-{bracket.chestInterval.maxCm}
                  </Text>
                )}
              </View>
            );
          })}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    marginBottom: 16,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 16,
  },
  categoryTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  brandSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  chartTag: {
    backgroundColor: "rgba(56, 189, 248, 0.12)",
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "rgba(56, 189, 248, 0.25)",
  },
  chartTagText: {
    fontSize: 9,
    fontWeight: "700",
    color: colors.textAccent,
    letterSpacing: 0.5,
  },
  badgeSection: {
    alignItems: "center",
    marginVertical: 8,
  },
  sizeBadge: {
    alignItems: "center",
    backgroundColor: "rgba(6, 182, 212, 0.08)",
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: "rgba(6, 182, 212, 0.35)",
    width: "100%",
  },
  sizeBadgeAbstain: {
    backgroundColor: "rgba(245, 158, 11, 0.1)",
    borderColor: "rgba(245, 158, 11, 0.3)",
  },
  sizeLabelPrefix: {
    fontSize: 11,
    fontWeight: "800",
    color: colors.primary,
    letterSpacing: 1,
  },
  sizeValue: {
    fontSize: 48,
    fontWeight: "900",
    color: colors.textPrimary,
    marginVertical: 4,
  },
  notesText: {
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: "center",
    marginTop: 2,
  },
  abstainTitle: {
    fontSize: 13,
    fontWeight: "800",
    color: colors.warning,
    letterSpacing: 0.5,
  },
  abstainReason: {
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: "center",
    marginTop: 6,
  },
  spectrumContainer: {
    marginTop: 14,
    borderTopWidth: 1,
    borderTopColor: "rgba(51, 65, 85, 0.4)",
    paddingTop: 12,
  },
  spectrumTitle: {
    fontSize: 11,
    fontWeight: "600",
    color: colors.textMuted,
    marginBottom: 8,
  },
  bracketsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  bracketPill: {
    alignItems: "center",
    paddingVertical: 6,
    paddingHorizontal: 4,
    borderRadius: 8,
    backgroundColor: "rgba(30, 41, 59, 0.5)",
    borderWidth: 1,
    borderColor: "rgba(51, 65, 85, 0.3)",
    flex: 1,
    marginHorizontal: 2,
  },
  bracketPillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  bracketSizeLabel: {
    fontSize: 12,
    fontWeight: "700",
    color: colors.textSecondary,
  },
  bracketSizeLabelActive: {
    color: "#04151F",
  },
  bracketRangeText: {
    fontSize: 8,
    color: colors.textMuted,
    marginTop: 2,
  },
  bracketRangeTextActive: {
    color: "#04151F",
    fontWeight: "600",
  },
});
