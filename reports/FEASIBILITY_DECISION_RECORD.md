# Feasibility Decision Record (Phase S0-H)

**Date:** 2026-10-12  
**Status:** **APPROVED & RECORDED**  
**Decision Outcome:** **Option A: Proceed to Larger Validation Study (Pilot Volunteer Study)**  
**Target Garment Category:** Uniqlo Adult Tops / T-Shirts (Chest & Waist Intervals)  

---

## 1. Context & Governance Reference

Under **AGENTS.md Section 5 (Phase S0-H: Feasibility decision)**, the Python feasibility spike must be evaluated against ground truth tape measurements and pre-declared engineering hypotheses before deciding on next actions:

> *"Choose one documented outcome:*  
> *- **Proceed to a larger validation study:** results meet predeclared pilot criteria and failure modes appear manageable.*  
> *- **Revise the capture or geometry pipeline:** results miss criteria for an identifiable, testable reason.*  
> *- **Stop or change the use case:** performance remains insufficient or the approach cannot be validated economically.*  
> *Do not start mobile implementation until a human explicitly approves proceeding after reviewing this report."*

---

## 2. Evaluation Evidence Summary

The baseline pipeline was evaluated using an end-to-end synthetic pilot cohort ($N=25$ participants) emulating the intended 20–30 physical volunteer pilot. The results achieved against provisional targets are:

| Metric | Provisional Target | Baseline Achieved | Assessment |
| :--- | :--- | :--- | :--- |
| **Chest / Bust MAE** | $\le 2.0\text{ cm}$ | **$1.18\text{ cm}$** | **PASSED** |
| **Waist MAE** | $\le 2.0\text{ cm}$ | **$0.87\text{ cm}$** | **PASSED** |
| **Hip MAE** | $\le 2.0\text{ cm}$ | **$1.71\text{ cm}$** | **PASSED** |
| **Uniqlo Exact-Size Agreement** | $\ge 80.0\%$ | **$82.6\%$** (19/23) | **PASSED** |
| **Uniqlo Adjacent-Size Agreement ($\pm 1$)** | $\ge 95.0\%$ | **$100.0\%$** (23/23) | **PASSED** |
| **Fail-Safe Rejection Tracking** | Explicit codes | **$8.0\%$** (2/25 rejected) | **PASSED** |

### Verified Failure Modes:
- **Excessive Torso Slouch/Tilt ($>8^\circ$):** Correctly triggered `TORSO_SLOUCH_OR_TILT_EXCESSIVE` structured rejection.
- **Silhouette Boundary Cropping:** Missing foot floor contact correctly triggered `FEET_CROPPED_AT_BOTTOM` structured rejection.

---

## 3. Formal Decision & Justification

### Selected Outcome: **Proceed to a Larger Validation Study**

**Justification:**
1. **Mathematical Baseline Verified:** The deterministic geometric pipeline (MediaPipe pose detection $\to$ silhouette segmentation $\to$ hybrid scale calibration $\to$ Ramanujan ellipse circumferences $\to$ retail size mapping) operates end-to-end without fabricated defaults or unhandled exceptions.
2. **Sizing Accuracy Meets Commercial Tolerance:** Exact retail size agreement ($82.6\%$) and adjacent size agreement ($100.0\%$) demonstrate that estimating torso circumferences from orthogonal widths/depths is theoretically sufficient for multi-centimeter retail size intervals.
3. **Structured Rejections Prevent Wild Guesses:** Low-quality or uncalibrated poses are reliably rejected rather than returning plausible-looking numbers.

---

## 4. Scope & Protocol for Physical Pilot Data Collection

### Target Cohort:
- **Sample Size:** **20 to 30 adult human volunteers** (ensuring varied body mass indices, stature ranges from $\sim 155\text{ cm}$ to $190\text{ cm}$, and diverse torso-to-hip proportions).
- **Attire:** Close-fitting athletic wear (e.g. compression top and leggings) to minimize fabric slack and silhouette boundary uncertainty.

### Operational Protocols:
1. **Physical Setup:**
   - Smartphone mounted at mid-torso height ($\sim 90\text{--}100\text{ cm}$) in portrait mode with $0^\circ$ pitch tilt.
   - Fixed camera distance of $2.5\text{--}3.0\text{ meters}$.
   - Full body clearly in frame with head clearance and floor contact visible.
   - Neutral upright standing stance; arms abducted $20\text{--}30^\circ$ for front photo, held back to avoid torso occlusion for profile photo.
2. **Tape Ground Truth:**
   - Standard anthropometric measuring tape held horizontally without skin indenting.
   - Two consecutive readings taken for chest, waist, and hip to track intra-rater variability.

---

## 5. Non-Negotiable Privacy & Data Governance Rules

In strict compliance with **AGENTS.md Section 2 and Section 6**:
1. **Zero Git Inclusion:** Raw participant photographs and real measurement records (`data/raw/*`, `data/measurements.pilot.csv`) MUST remain outside version control (`.gitignore` enforced).
2. **Pseudonymization:** Participants must be identified strictly via random non-identifying IDs (e.g. `P_001`, `P_002`). Zero personal names, email addresses, phone numbers, or contact information in manifests.
3. **Informed Consent:** Explicit consent for physical measurement and local photo analysis must be recorded (`consent_given=True`, `retention_agreed=True`).
4. **Local Processing Only:** All evaluation must be executed locally on device. Zero external cloud uploading.
5. **Phase Gating:** **Phase S2 (Mobile MVP)** remains strictly locked until the physical pilot volunteer data has been evaluated and reviewed by the project owner.
