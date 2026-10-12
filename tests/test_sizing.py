"""Unit tests for garment size chart encoding, boundary ties, and sizing accuracy evaluation."""

import pytest

from body_measurement.sizing import (
    UNIQLO_ADULT_TOPS_CHART,
    are_adjacent_sizes,
    evaluate_sizing_performance,
    recommend_size,
)


def test_uniqlo_chart_metadata():
    """Verify Uniqlo size chart metadata and continuous coverage."""
    chart = UNIQLO_ADULT_TOPS_CHART
    assert chart.brand == "Uniqlo"
    assert "T-Shirts" in chart.garment_category
    assert chart.retrieval_date == "2026-10-12"
    assert chart.ordered_sizes == ["XS", "S", "M", "L", "XL", "XXL"]
    assert len(chart.brackets) == 6


def test_recommend_size_standard():
    """Verify normal sizing mapping."""
    # Chest 95.0 cm, Waist 82.0 cm falls cleanly into M (92-100 cm)
    rec = recommend_size(chest_cm=95.0, waist_cm=82.0)
    assert rec.status == "RECOMMENDED"
    assert rec.recommended_size == "M"
    assert rec.chest_size == "M"
    assert rec.waist_size == "M"


def test_recommend_size_upper_boundary_tie():
    """Verify upper size preference on exact boundary ties (comfort fit)."""
    # 92.0 cm is the boundary between S (84-92) and M (92-100)
    rec = recommend_size(chest_cm=92.0)
    assert rec.recommended_size == "M"

    # 100.0 cm is the boundary between M and L
    rec2 = recommend_size(chest_cm=100.0)
    assert rec2.recommended_size == "L"


def test_recommend_size_accommodating_fit():
    """Verify sizing up to accommodate larger waist dimension."""
    # Chest 90.0 cm suggests S (84-92), but Waist 84.0 cm suggests M (80-88)
    rec = recommend_size(chest_cm=90.0, waist_cm=84.0)
    assert rec.recommended_size == "M"
    assert "Accommodating fit" in rec.notes


def test_recommend_size_out_of_bounds_abstain():
    """Verify measurements outside chart range trigger structured abstention."""
    # Below XS (< 78 cm)
    rec_low = recommend_size(chest_cm=70.0)
    assert rec_low.status == "ABSTAIN_OUT_OF_BOUNDS"
    assert rec_low.recommended_size is None

    # Above XXL (> 128 cm)
    rec_high = recommend_size(chest_cm=135.0)
    assert rec_high.status == "ABSTAIN_OUT_OF_BOUNDS"
    assert rec_high.recommended_size is None

    # Missing / None
    rec_none = recommend_size(chest_cm=None)
    assert rec_none.status == "ABSTAIN_MISSING_INPUT"
    assert rec_none.recommended_size is None


def test_are_adjacent_sizes():
    """Verify adjacency calculation across size sequence."""
    assert are_adjacent_sizes("M", "M") is True
    assert are_adjacent_sizes("S", "M") is True
    assert are_adjacent_sizes("M", "L") is True
    assert are_adjacent_sizes("S", "L") is False
    assert are_adjacent_sizes("XS", "XXL") is False
    assert are_adjacent_sizes("INVALID", "M") is False


def test_evaluate_sizing_performance():
    """Verify sizing performance aggregation, accuracy, and confusion matrix."""
    comparisons = [
        # Exact match (M == M)
        {"participant_id": "P1", "ref_chest_cm": 95.0, "ref_waist_cm": 82.0, "pred_chest_cm": 96.0, "pred_waist_cm": 83.0},
        # Adjacent match (ref S, pred M)
        {"participant_id": "P2", "ref_chest_cm": 88.0, "ref_waist_cm": 75.0, "pred_chest_cm": 93.0, "pred_waist_cm": 81.0},
        # Distant mismatch (ref S, pred L)
        {"participant_id": "P3", "ref_chest_cm": 88.0, "ref_waist_cm": 75.0, "pred_chest_cm": 102.0, "pred_waist_cm": 90.0},
        # Abstention (pred out of bounds)
        {"participant_id": "P4", "ref_chest_cm": 95.0, "ref_waist_cm": 82.0, "pred_chest_cm": 140.0, "pred_waist_cm": 120.0},
    ]

    res = evaluate_sizing_performance(comparisons)
    assert res.total_participants == 4
    assert res.evaluated_count == 3
    assert res.exact_matches == 1
    assert res.adjacent_matches == 1
    # Exact accuracy: 1 / 3 = 33.3%
    assert res.exact_accuracy_pct == 33.3
    # Adjacent accuracy: (1 + 1) / 3 = 66.7%
    assert res.adjacent_accuracy_pct == 66.7
    assert res.abstention_count == 1
    assert res.abstention_rate_pct == 25.0
    assert res.coverage_rate_pct == 75.0

    # Verify confusion matrix
    assert res.confusion_matrix["M"]["M"] == 1
    assert res.confusion_matrix["S"]["M"] == 1
    assert res.confusion_matrix["S"]["L"] == 1
    assert res.confusion_matrix["M"]["ABSTAIN"] == 1
