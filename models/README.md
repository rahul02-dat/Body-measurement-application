# Models Directory & Provenance

This directory documents model assets, versions, licenses, and download instructions for the body measurement feasibility spike.

Model binary files (`*.task`, `*.onnx`, `*.tflite`) are excluded from version control via `.gitignore` and must be acquired through the documented source below.

---

## 1. Candidate Pose & Segmentation Model

For the Python feasibility spike, the primary candidate model is the **MediaPipe Pose Landmarker** with integrated segmentation mask output.

- **Model Name**: MediaPipe Pose Landmarker (`pose_landmarker_full.task` / `pose_landmarker_heavy.task`)
- **Developer / Publisher**: Google
- **Source Documentation**: [MediaPipe Pose Landmarker Python Guide](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python)
- **License**: Apache License 2.0
- **Model Storage Target**: `models/pose_landmarker_full.task`

### Available Model Variants

| Variant | Filename | Download URL | Recommended Use |
| :--- | :--- | :--- | :--- |
| **Full** *(Default)* | `pose_landmarker_full.task` | `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task` | Balanced accuracy and speed; suitable for static high-res photo landmarking. |
| **Heavy** | `pose_landmarker_heavy.task` | `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task` | Highest accuracy landmark localization and confidence. |
| **Lite** | `pose_landmarker_lite.task` | `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task` | Lower compute; not recommended for geometric estimation. |

---

## 2. Download Instructions

To download the default model bundle into this directory:

```bash
curl -o models/pose_landmarker_full.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
```

### Configuration Parameters
When instantiated in Phase S0-C:
- `running_mode`: `IMAGE`
- `output_segmentation_masks`: `True`
- `min_pose_detection_confidence`: `0.7`
- `min_pose_presence_confidence`: `0.7`
- `min_tracking_confidence`: `0.7`

---

## 3. Phase S1 Calibration Regression Models

- **Asset Path**: `models/calibration_models.json`
- **Model Type**: Ridge Regression ($\alpha = 1.0$) with feature z-score standardization
- **Training Cohort**: US Army Anthropometric Survey (ANSUR II, 2012, Natick TR-15/007; $N = 4,854$ training subjects, 5-fold cross-validation)
- **Held-Out Test Set**: $N = 1,214$ untouched held-out subjects
- **License / Provenance**: Public Domain (U.S. Federal Government Research)
- **Features Used**:
  - `chest`: `[chest_ramanujan_cm, height_cm, weight_kg]`
  - `waist`: `[waist_ramanujan_cm, height_cm, weight_kg]`
- **Validation Report**: [`reports/ANSUR_CALIBRATION_REPORT.md`](../reports/ANSUR_CALIBRATION_REPORT.md)

