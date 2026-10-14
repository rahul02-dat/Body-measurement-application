# Feasibility Spike Baseline Evaluation Report

> **Notice:** Experimental evaluation comparing photo-based Ramanujan ellipse approximations against physical tape measurements.

## 1. Evaluation Sample Counts & Quality Overview

- **Total Manifest Records:** 25
- **Successful Estimates:** 23
- **Rejected Records:** 2 (8.0% failure/rejection rate)

### Failure / Rejection Reasons Breakdown:
- `TORSO_SLOUCH_OR_TILT_EXCESSIVE (9.4° > 8.0°)`: 1 case(s)
- `FEET_CROPPED_AT_BOTTOM`: 1 case(s)

## 2. Circumference Accuracy Metrics

| Anatomical Landmark | Evaluated N | MAE (cm) | Median AE (cm) | Signed Bias (cm) | P90 AE (cm) | RMSE (cm) | <= 1cm (%) | <= 2cm (%) (Target) | <= 3cm (%) | <= 5cm (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Chest** | 23 | 1.18 | 1.20 | +1.05 | 2.08 | 1.46 | 43.5% | **87.0%** | 95.7% | 100.0% |
| **Waist** | 23 | 0.87 | 0.90 | +0.52 | 1.60 | 1.05 | 65.2% | **100.0%** | 100.0% | 100.0% |
| **Hip** | 23 | 1.71 | 1.80 | +1.69 | 2.50 | 1.87 | 17.4% | **60.9%** | 100.0% | 100.0% |

## 3. Intra-Rater Tape Measurement Variability

| Measurement | Sample Count | Mean Abs Diff (cm) | Max Abs Diff (cm) | Std Diff (cm) |
| :--- | :--- | :--- | :--- | :--- |
| **Chest** | 25 | 0.16 | 0.40 | 0.13 |
| **Waist** | 25 | 0.17 | 0.40 | 0.13 |
| **Hip** | 25 | 0.18 | 0.50 | 0.14 |

## 4. Garment Size-Chart Recommendation Evaluation

- **Target Brand:** Uniqlo
- **Garment Category:** Adult Tops / T-Shirts
- **Exact-Size Agreement:** **82.6%** (19/23) [Provisional Target: >= 80%]
- **Adjacent-Size Agreement (±1 size):** **100.0%** (23/23) [Provisional Target: >= 95%]
- **Abstention Rate:** 8.0% (2/25)
- **Recommendation Coverage:** 92.0%

### Size Recommendation Confusion Matrix (Reference vs Predicted):

| Ref \ Pred | XS | S | M | L | XL | XXL | ABSTAIN |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **XS** | 1 | 2 | 0 | 0 | 0 | 0 | 0 |
| **S** | 0 | 6 | 1 | 0 | 0 | 0 | 0 |
| **M** | 0 | 0 | 5 | 0 | 0 | 0 | 2 |
| **L** | 0 | 0 | 0 | 3 | 1 | 0 | 0 |
| **XL** | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| **XXL** | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| **ABSTAIN** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## 5. Key Limitations & Assumptions Disclosed

1. **Ramanujan Ellipse Model:** Real human body cross-sections are irregular non-elliptical geometries; approximating them with orthogonal widths and depths creates an inherent geometric modeling error.
2. **Attire & Slack:** Clothing thickness or fabric bunching introduces radial bias into the silhouette boundary.
3. **Height Scale Anchor:** Calibration is entirely scaled by user-reported height. Incorrect height entries directly scale all circumferences proportionally.
4. **Perspective & Pose Inconsistency:** Camera pitch tilt, subject distance variations, and stance shifts between front and side photos induce projection distortion.

## 6. Diagnostic Error Plots

- **Tape vs predicted scatter:** `plots/tape_vs_predicted_scatter.png`
- **Error distribution histograms:** `plots/error_distribution_histograms.png`
- **Bland altman plots:** `plots/bland_altman_plots.png`

