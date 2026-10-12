# Photo-Based Body Measurement Feasibility Spike

A research-first evaluation spike investigating whether two guided smartphone photographs (front and side) plus self-reported height can support reliable clothing-size recommendations.

> **Status:** Phase S0-A (Repository and Protocol Setup)  
> **Experimental System Disclaimer:** This project is strictly experimental. Estimated measurements are **not** presented as exact, clinically validated, or suitable for bespoke tailoring. The primary goal is assessing whether photo-derived dimensions can reliably predict garment sizing for retail charts.

---

## 1. Project Overview & Scope

### In Scope for the Feasibility Spike
- A front photograph and a profile/side photograph captured under a documented protocol.
- User-entered standing height as the initial scale anchor.
- Pose landmarks and person segmentation via MediaPipe Pose Landmarker.
- Torso cross-section approximations (chest/bust, waist, hip circumferences) via Ramanujan's ellipse approximation.
- Shoulder width and inseam as exploratory measurements.
- Ground truth comparison against physical tape measurements.
- Evaluation metrics: Mean Absolute Error (MAE), median error, signed bias, 90th percentile error, and garment size-chart recommendation accuracy (exact & ±1 adjacent size).
- Structured diagnostic failure modes and overlays.

### Out of Scope Until Approved
- Claims of tailoring-grade or clinical measurement precision.
- Body-fat or fitness composition estimation.
- 3D parametric mesh reconstruction or 3D avatar generation.
- Production mobile applications, cloud synchronization, user accounts, or payments.
- Automatic training or continuous model updates from user corrections without governed pipelines.

---

## 2. Environment Setup

The spike is built with Python 3.12 (compatible with Python >= 3.10).

### Virtual Environment & Installation

```bash
# 1. Activate your existing virtual environment (or create one):
# python -m venv env
source env/bin/activate

# 2. Upgrade pip and build tools
pip install --upgrade pip setuptools wheel

# 3. Install the package in editable mode with development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run test suite with pytest
pytest -v
```

---

## 3. Data Protocols & Guidelines

Comprehensive details on the data schema, measurement instructions, and privacy rules are documented in [`data/README.md`](data/README.md).

### Summary Protocols:
1. **Physical Tape Measurements**:
   - **Chest / Bust**: Measured horizontally across the fullest point of the bust/chest during normal, relaxed breathing.
   - **Waist**: Measured horizontally at the natural waistline (narrowest torso constriction, ~2–3 cm above navel) at the end of normal exhalation.
   - **Hip**: Measured horizontally around the maximum protrusion of the buttocks with heels together.
   - **Repeat Readings**: Intra-rater variation assessed with two consecutive readings per landmark.
2. **Photo Capture Protocol**:
   - **Device & Alignment**: Smartphone mounted at mid-torso height (~90–100 cm) in portrait mode, level (no tilt).
   - **Distance**: 2.5–3.0 meters from subject.
   - **Framing**: Full body clearly framed with margin above head and feet touching floor visible.
   - **Attire**: Form-fitting athletic clothing (leggings/compression shirt) to eliminate fabric slack.
   - **Poses**: Upright, neutral standing posture. Front pose with arms slightly separated from torso (20–30° angle). Side pose with arms held back to prevent torso occlusion.
3. **Privacy & Governance**:
   - Zero raw participant imagery or personal data committed to version control.
   - Anonymized identifiers only (`P001`, `P002`, ...).
   - Strictly local file storage under `data/raw/` (ignored by `.gitignore`).

---

## 4. Models & Asset Provenance

Details on model licenses, download links, and configurations are documented in [`models/README.md`](models/README.md).

The candidate pose and segmentation model is **MediaPipe Pose Landmarker** (`pose_landmarker_full.task`), published under the Apache 2.0 license.

To download the model bundle for Phase S0-C:
```bash
curl -o models/pose_landmarker_full.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
```

---

## 5. Repository Layout

```text
├── AGENTS.md                  # Project constitution and phase roadmap
├── README.md                  # Project overview, protocol summary & setup guide
├── pyproject.toml             # Python package configuration and dependencies
├── .gitignore                 # Exclusion rules for data, models, environments, docs
├── data/
│   ├── README.md              # Detailed measurement protocol, schema & privacy rules
│   └── measurements.example.csv # Synthetic example data schema
├── models/
│   └── README.md              # Model provenance, licenses, and download instructions
├── notebooks/
│   └── README.md              # Notebook analysis workspace guidelines
├── src/
│   └── body_measurement/     # Core package source code
│       └── __init__.py
└── tests/
    ├── __init__.py
    └── test_setup.py          # Environment and schema verification tests
```

---

## 6. Implementation Phases Roadmap

- [x] **Phase S0-A**: Repository and protocol setup
- [x] **Phase S0-B**: Data schema validation & safe image loading
- [x] **Phase S0-C**: Pose detection and segmentation pipeline
- [x] **Phase S0-D**: Scale calibration (pixels-per-cm via height)
- [ ] **Phase S0-E**: Geometric baseline (Ramanujan ellipse approximation)
- [ ] **Phase S0-F**: Evaluation against ground-truth tape measurements
- [ ] **Phase S0-G**: Size-chart evaluation & recommendation accuracy
- [ ] **Phase S0-H**: Feasibility Gate Review (Decision: Proceed / Revise / Stop)
- [ ] **Phase S1**: Optional calibration regression experiments
- [ ] **Phase S2**: Mobile MVP (only after human approval)
