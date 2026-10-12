"""Garment size chart encoding, deterministic size derivation, and recommendation evaluation."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


@dataclass(frozen=True)
class SizeInterval:
    """A 1D continuous metric range [min_cm, max_cm) or (min_cm, max_cm]."""

    min_cm: float
    max_cm: float

    def contains(self, value: float, tie_preference: str = "upper") -> bool:
        """
        Check if value falls within interval.

        Tie breaking rule (per project specification):
        If tie_preference == "upper", on exact lower boundary the value belongs to this (higher) bracket.
        Interval definition: [min_cm, max_cm) for intermediate sizes, with exact boundary falling into upper bracket.
        """
        if tie_preference == "upper":
            # [min_cm, max_cm) - inclusive lower, exclusive upper
            return self.min_cm <= value < self.max_cm
        else:
            # (min_cm, max_cm] - exclusive lower, inclusive upper
            return self.min_cm < value <= self.max_cm


@dataclass(frozen=True)
class SizeBracket:
    """A discrete garment size bracket with chest and optional waist intervals."""

    size_label: str
    chest_interval: SizeInterval
    waist_interval: Optional[SizeInterval] = None


@dataclass
class SizeChart:
    """Encoded garment size chart specification with documented provenance."""

    brand: str
    garment_category: str
    source_url: str
    retrieval_date: str
    measurement_unit: str
    ordered_sizes: List[str]
    brackets: List[SizeBracket]

    def get_size_index(self, size_label: str) -> Optional[int]:
        """Return 0-indexed position of size label in ascending ordered sequence."""
        try:
            return self.ordered_sizes.index(size_label)
        except ValueError:
            return None


# Encoded Uniqlo Adult Tops / T-Shirts Size Chart
# Source: Official Uniqlo published size chart for Adult Crew Neck T-Shirts / Tops
# Retrieval Date: 2026-10-12
UNIQLO_ADULT_TOPS_CHART = SizeChart(
    brand="Uniqlo",
    garment_category="Adult Tops / T-Shirts",
    source_url="https://www.uniqlo.com/us/en/size/422992.html",
    retrieval_date="2026-10-12",
    measurement_unit="cm",
    ordered_sizes=["XS", "S", "M", "L", "XL", "XXL"],
    brackets=[
        SizeBracket(
            size_label="XS",
            chest_interval=SizeInterval(min_cm=78.0, max_cm=84.0),
            waist_interval=SizeInterval(min_cm=66.0, max_cm=72.0),
        ),
        SizeBracket(
            size_label="S",
            chest_interval=SizeInterval(min_cm=84.0, max_cm=92.0),
            waist_interval=SizeInterval(min_cm=72.0, max_cm=80.0),
        ),
        SizeBracket(
            size_label="M",
            chest_interval=SizeInterval(min_cm=92.0, max_cm=100.0),
            waist_interval=SizeInterval(min_cm=80.0, max_cm=88.0),
        ),
        SizeBracket(
            size_label="L",
            chest_interval=SizeInterval(min_cm=100.0, max_cm=108.0),
            waist_interval=SizeInterval(min_cm=88.0, max_cm=96.0),
        ),
        SizeBracket(
            size_label="XL",
            chest_interval=SizeInterval(min_cm=108.0, max_cm=116.0),
            waist_interval=SizeInterval(min_cm=96.0, max_cm=104.0),
        ),
        SizeBracket(
            size_label="XXL",
            chest_interval=SizeInterval(min_cm=116.0, max_cm=128.0),
            waist_interval=SizeInterval(min_cm=104.0, max_cm=116.0),
        ),
    ],
)


@dataclass
class SizeRecommendation:
    """Deterministic size recommendation output."""

    recommended_size: Optional[str]
    chest_size: Optional[str]
    waist_size: Optional[str]
    status: str  # "RECOMMENDED", "ABSTAIN_OUT_OF_BOUNDS", "ABSTAIN_MISSING_INPUT"
    abstention_reason: Optional[str] = None
    notes: str = ""


def _match_single_dimension(value_cm: float, brackets: List[SizeBracket], dim: str = "chest") -> Optional[str]:
    """Find matching bracket for a single dimension using upper boundary tie preference."""
    for bracket in brackets:
        interval = bracket.chest_interval if dim == "chest" else bracket.waist_interval
        if interval is not None and interval.contains(value_cm, tie_preference="upper"):
            return bracket.size_label

    # Check edge limits: if exactly at top of largest bracket
    largest = brackets[-1]
    largest_interval = largest.chest_interval if dim == "chest" else largest.waist_interval
    if largest_interval and value_cm == largest_interval.max_cm:
        return largest.size_label

    return None


def recommend_size(
    chest_cm: Optional[float],
    waist_cm: Optional[float] = None,
    chart: SizeChart = UNIQLO_ADULT_TOPS_CHART,
    tie_preference: str = "upper",
) -> SizeRecommendation:
    """
    Derive deterministic size recommendation from body dimensions.

    Rules:
    1. If chest is missing or non-positive: ABSTAIN_MISSING_INPUT.
    2. Exact boundary ties: Resolves to the larger size bracket (per user specification).
    3. Multi-dimension conflict: Uses accommodating fit (sizes up to fit the larger dimension).
    4. Out of chart bounds: ABSTAIN_OUT_OF_BOUNDS.
    """
    if chest_cm is None or chest_cm <= 0:
        return SizeRecommendation(
            recommended_size=None,
            chest_size=None,
            waist_size=None,
            status="ABSTAIN_MISSING_INPUT",
            abstention_reason="Missing or invalid chest measurement.",
        )

    chest_size = _match_single_dimension(chest_cm, chart.brackets, dim="chest")
    waist_size = _match_single_dimension(waist_cm, chart.brackets, dim="waist") if waist_cm else None

    # Handle chest out of chart bounds
    min_chest = chart.brackets[0].chest_interval.min_cm
    max_chest = chart.brackets[-1].chest_interval.max_cm

    if chest_cm < min_chest:
        return SizeRecommendation(
            recommended_size=None,
            chest_size=None,
            waist_size=waist_size,
            status="ABSTAIN_OUT_OF_BOUNDS",
            abstention_reason=f"Chest ({chest_cm:.1f}cm) is below chart range (<{min_chest:.1f}cm).",
        )
    if chest_cm > max_chest:
        return SizeRecommendation(
            recommended_size=None,
            chest_size=None,
            waist_size=waist_size,
            status="ABSTAIN_OUT_OF_BOUNDS",
            abstention_reason=f"Chest ({chest_cm:.1f}cm) is above chart range (>{max_chest:.1f}cm).",
        )

    # Accommodating fit rule: pick the larger size between chest and waist
    if chest_size is not None and waist_size is not None:
        idx_chest = chart.get_size_index(chest_size)
        idx_waist = chart.get_size_index(waist_size)
        if idx_chest is not None and idx_waist is not None:
            if idx_waist > idx_chest:
                final_size = waist_size
                notes = f"Accommodating fit: sized up to {waist_size} for waist ({waist_cm:.1f}cm)."
            else:
                final_size = chest_size
                notes = f"Fit driven by chest dimension ({chest_cm:.1f}cm)."
        else:
            final_size = chest_size
            notes = "Fit driven by chest dimension."
    else:
        final_size = chest_size
        notes = "Fit determined by chest dimension alone."

    return SizeRecommendation(
        recommended_size=final_size,
        chest_size=chest_size,
        waist_size=waist_size,
        status="RECOMMENDED",
        notes=notes,
    )


def are_adjacent_sizes(size_a: str, size_b: str, chart: SizeChart = UNIQLO_ADULT_TOPS_CHART) -> bool:
    """Return True if size_a and size_b are identical or adjacent within 1 size step."""
    idx_a = chart.get_size_index(size_a)
    idx_b = chart.get_size_index(size_b)
    if idx_a is None or idx_b is None:
        return False
    return abs(idx_a - idx_b) <= 1


@dataclass
class SizingEvaluationResult:
    """Comprehensive evaluation metrics comparing image-derived size with tape reference size."""

    chart_brand: str
    chart_category: str
    total_participants: int
    evaluated_count: int
    exact_matches: int
    adjacent_matches: int
    exact_accuracy_pct: float
    adjacent_accuracy_pct: float
    abstention_count: int
    abstention_rate_pct: float
    coverage_rate_pct: float
    confusion_matrix: Dict[str, Dict[str, int]]
    participant_comparisons: List[Dict[str, Any]] = field(default_factory=list)


def evaluate_sizing_performance(
    comparisons: List[Dict[str, Any]],
    chart: SizeChart = UNIQLO_ADULT_TOPS_CHART,
) -> SizingEvaluationResult:
    """
    Evaluate sizing recommendations comparing tape ground truth with image estimates.

    Each dict in comparisons must contain:
    - participant_id: str
    - ref_chest_cm: float
    - ref_waist_cm: Optional[float]
    - pred_chest_cm: Optional[float]
    - pred_waist_cm: Optional[float]
    """
    total = len(comparisons)
    exact_matches = 0
    adjacent_matches = 0
    abstention_count = 0
    evaluated_count = 0

    # Initialize confusion matrix: [ref_size][pred_size]
    matrix: Dict[str, Dict[str, int]] = {
        s: {p: 0 for p in chart.ordered_sizes + ["ABSTAIN"]}
        for s in chart.ordered_sizes + ["ABSTAIN"]
    }

    results_list: List[Dict[str, Any]] = []

    for item in comparisons:
        pid = item["participant_id"]
        ref_rec = recommend_size(item.get("ref_chest_cm"), item.get("ref_waist_cm"), chart=chart)
        pred_rec = recommend_size(item.get("pred_chest_cm"), item.get("pred_waist_cm"), chart=chart)

        ref_s = ref_rec.recommended_size or "ABSTAIN"
        pred_s = pred_rec.recommended_size or "ABSTAIN"

        matrix[ref_s][pred_s] = matrix[ref_s].get(pred_s, 0) + 1

        is_exact = False
        is_adjacent = False
        if ref_s != "ABSTAIN" and pred_s != "ABSTAIN":
            evaluated_count += 1
            if ref_s == pred_s:
                exact_matches += 1
                is_exact = True
                is_adjacent = True
            elif are_adjacent_sizes(ref_s, pred_s, chart=chart):
                adjacent_matches += 1
                is_adjacent = True
        else:
            abstention_count += 1

        results_list.append({
            "participant_id": pid,
            "ref_size": ref_s,
            "pred_size": pred_s,
            "is_exact": is_exact,
            "is_adjacent": is_adjacent,
            "ref_notes": ref_rec.notes or ref_rec.abstention_reason,
            "pred_notes": pred_rec.notes or pred_rec.abstention_reason,
        })

    exact_acc = round(exact_matches / evaluated_count * 100.0, 1) if evaluated_count > 0 else 0.0
    adjacent_acc = round((exact_matches + adjacent_matches) / evaluated_count * 100.0, 1) if evaluated_count > 0 else 0.0
    abstention_rate = round(abstention_count / total * 100.0, 1) if total > 0 else 0.0
    coverage_rate = round(100.0 - abstention_rate, 1)

    return SizingEvaluationResult(
        chart_brand=chart.brand,
        chart_category=chart.garment_category,
        total_participants=total,
        evaluated_count=evaluated_count,
        exact_matches=exact_matches,
        adjacent_matches=adjacent_matches,
        exact_accuracy_pct=exact_acc,
        adjacent_accuracy_pct=adjacent_acc,
        abstention_count=abstention_count,
        abstention_rate_pct=abstention_rate,
        coverage_rate_pct=coverage_rate,
        confusion_matrix=matrix,
        participant_comparisons=results_list,
    )
