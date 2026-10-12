import {
  areAdjacentSizes,
  recommendSize,
  UNIQLO_ADULT_TOPS_CHART,
} from "../src/engine/sizing";

describe("Uniqlo Retail Sizing Engine", () => {
  test("chart metadata has continuous coverage across 6 brackets", () => {
    expect(UNIQLO_ADULT_TOPS_CHART.brand).toBe("Uniqlo");
    expect(UNIQLO_ADULT_TOPS_CHART.orderedSizes).toEqual([
      "XS",
      "S",
      "M",
      "L",
      "XL",
      "XXL",
    ]);
    expect(UNIQLO_ADULT_TOPS_CHART.brackets).toHaveLength(6);
  });

  test("standard measurement recommendation matches expected size", () => {
    // Chest 95.0 cm, Waist 82.0 cm falls cleanly into M (92-100 cm)
    const rec = recommendSize(95.0, 82.0);
    expect(rec.status).toBe("RECOMMENDED");
    expect(rec.recommendedSize).toBe("M");
    expect(rec.chestSize).toBe("M");
    expect(rec.waistSize).toBe("M");
  });

  test("exact boundary tie resolves to upper bracket (comfort fit)", () => {
    // 92.0 cm is boundary between S (84-92) and M (92-100) -> M
    const rec1 = recommendSize(92.0);
    expect(rec1.recommendedSize).toBe("M");

    // 100.0 cm is boundary between M (92-100) and L (100-108) -> L
    const rec2 = recommendSize(100.0);
    expect(rec2.recommendedSize).toBe("L");
  });

  test("accommodating fit sizes up when waist requires larger size", () => {
    // Chest 90.0 cm suggests S (84-92), but Waist 84.0 cm suggests M (80-88)
    const rec = recommendSize(90.0, 84.0);
    expect(rec.status).toBe("RECOMMENDED");
    expect(rec.recommendedSize).toBe("M");
    expect(rec.notes).toContain("Accommodating fit: sized up to M");
  });

  test("out of bounds measurements trigger structured abstention", () => {
    // Below XS (< 78 cm)
    const recLow = recommendSize(70.0);
    expect(recLow.status).toBe("ABSTAIN_OUT_OF_BOUNDS");
    expect(recLow.recommendedSize).toBeNull();
    expect(recLow.abstentionReason).toContain("below smallest chart size");

    // Above XXL (> 128 cm)
    const recHigh = recommendSize(135.0);
    expect(recHigh.status).toBe("ABSTAIN_OUT_OF_BOUNDS");
    expect(recHigh.recommendedSize).toBeNull();
    expect(recHigh.abstentionReason).toContain("above largest chart size");

    // Missing / invalid
    const recNone = recommendSize(null);
    expect(recNone.status).toBe("ABSTAIN_MISSING_INPUT");
    expect(recNone.recommendedSize).toBeNull();
  });

  test("areAdjacentSizes verifies immediate neighbor relationships", () => {
    expect(areAdjacentSizes("M", "M")).toBe(true);
    expect(areAdjacentSizes("S", "M")).toBe(true);
    expect(areAdjacentSizes("M", "L")).toBe(true);
    expect(areAdjacentSizes("S", "L")).toBe(false);
    expect(areAdjacentSizes("XS", "XXL")).toBe(false);
    expect(areAdjacentSizes("INVALID", "M")).toBe(false);
  });
});
