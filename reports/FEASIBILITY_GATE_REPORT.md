# Phase S0-H: Feasibility Gate Evaluation Report

> **Project:** Photo-Based Body Measurement Feasibility Spike  
> **Evaluation Mode:** Synthetic Pilot Cohort (N=25 Participants)  
> **Target Retail Brand:** Uniqlo (Adult Tops / T-Shirts)  
> **Reference Protocol:** Ramanujan Ellipse Baseline vs Ground Truth Tape Measurements  

---

## 1. Executive Summary & Provisional Criteria Assessment

According to **AGENTS.md Section 5 (Phase S0-H)**, the baseline feasibility is evaluated against provisional engineering targets before deciding to proceed, revise, or stop:

| Target Metric | Provisional Target | Achieved Result | Gate Status |
| :--- | :--- | :--- | :--- |
| **Chest Circumference MAE** | `<= 2.0 cm` | **1.18 cm** | ✅ PASS |
| **Waist Circumference MAE** | `<= 2.0 cm` | **0.87 cm** | ✅ PASS |
| **Hip Circumference MAE** | `<= 2.0 cm` | **1.71 cm** | ✅ PASS |
| **Uniqlo Exact-Size Agreement** | `>= 80.0%` | **82.6%** (19/23) | ✅ PASS |
| **Uniqlo Adjacent-Size Agreement (±1)** | `>= 95.0%` | **100.0%** (4/23) | ✅ PASS |
| **Fail-Safe Rejection Tracking** | Explicit codes | **8.0%** (2/25) | ✅ PASS |

---

## 2. Circumference Accuracy Analysis

Detailed statistical distribution across evaluated landmarks:

| Landmark | Evaluated N | MAE (cm) | Median AE (cm) | Signed Bias (cm) | P90 AE (cm) | RMSE (cm) | <= 1cm (%) | <= 2cm (%) | <= 3cm (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Chest / Bust** | 23 | 1.18 | 1.20 | +1.05 | 2.08 | 1.46 | 43.5% | 87.0% | 95.7% |
| **Waist** | 23 | 0.87 | 0.90 | +0.52 | 1.60 | 1.05 | 65.2% | 100.0% | 100.0% |
| **Hip** | 23 | 1.71 | 1.80 | +1.69 | 2.50 | 1.87 | 17.4% | 60.9% | 100.0% |

---

## 3. Retail Sizing Recommendation Performance (Uniqlo Tops)

- **Target Brand:** Uniqlo Adult Tops / T-Shirts (Chest & Waist intervals)
- **Exact-Size Agreement:** **82.6%**
- **Adjacent-Size Agreement (±1 size):** **100.0%**
- **Abstention Rate:** **8.0%**
- **Recommendation Coverage:** **92.0%**

### Sizing Confusion Matrix (Reference vs Predicted):

| Ref \ Pred | XS | S | M | L | XL | XXL | ABSTAIN |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **XS** | 1 | 2 | 0 | 0 | 0 | 0 | 0 |
| **S** | 0 | 6 | 1 | 0 | 0 | 0 | 0 |
| **M** | 0 | 0 | 5 | 0 | 0 | 0 | 2 |
| **L** | 0 | 0 | 0 | 3 | 1 | 0 | 0 |
| **XL** | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| **XXL** | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| **ABSTAIN** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

---

## 4. Structured Fail-Safe Rejections Breakdown

Out of 25 participant records, 2 were safely rejected:
- `TORSO_SLOUCH_OR_TILT_EXCESSIVE (9.4° > 8.0°)`: **1 case(s)**
- `FEET_CROPPED_AT_BOTTOM`: **1 case(s)**

---

## 5. Artifacts Generated

- **Predictions CSV:** `reports/per_participant_predictions.csv`
- **Baseline Report:** `reports/baseline_evaluation_report.md`
- **Metrics JSON:** `reports/metrics_summary.json`
- **Diagnostic Plots:**
  - `circumference_error_distributions.png`
  - `ground_truth_vs_predicted_scatter.png`
  - `bland_altman_plots.png`

---

## 6. Phase S0-H Feasibility Gate Decision Record

Under **AGENTS.md Section 5 (Phase S0-H)**, one of three formal decisions must be documented:

### Option A: Proceed to a Larger Validation Study
- **Rationale:** The mathematical baseline, Ramanujan ellipse geometry, Uniqlo size chart logic, and fail-safe rejection gates are verified end-to-end. Circumference errors and adjacent-size accuracies meet the provisional target bounds.
- **Next Action:** Collect real pilot volunteer photographs (20–30 subjects) under the documented physical protocol and run baseline evaluation against real tape ground truth.

### Option B: Revise the Capture or Geometry Pipeline
- **Rationale:** If pilot data reveals systematic biases due to clothing slack, camera perspective tilt, or non-elliptical torso cross-sections.
- **Next Action:** Refine silhouette extraction or investigate Phase S1 linear calibration on training splits.

### Option C: Stop or Change Use Case
- **Rationale:** If physical testing demonstrates that two 2D photos cannot achieve commercially viable sizing accuracy.

> **Enforcement Rule:** In strict accordance with AGENTS.md Rule 3, **do NOT start mobile implementation (Phase S2)** until real volunteer data is evaluated and a human explicitly signs off.
