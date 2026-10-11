# Data Protocol, Dictionary & Privacy Procedures

This directory documents the participant measurement schema, the physical tape measurement protocol, photo capture specifications, and data privacy safeguards for the body measurement feasibility spike.

---

## 1. Data Schema & Dictionary

The baseline dataset schema is demonstrated in [`measurements.example.csv`](measurements.example.csv). Real participant records must follow this exact structure and be stored in local non-versioned storage (e.g., `data/raw/` or `data/participants/`).

| Field Name | Type | Unit / Format | Required | Description | Missing Value Policy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `participant_id` | String | Format: `P[0-9]{3}` | Yes | Anonymous participant identifier (randomized, non-identifying). | Never allowed to be missing. |
| `front_image_path` | String | Relative path | Yes | Relative path to local front-view JPEG/PNG photo. | Never allowed to be missing. |
| `side_image_path` | String | Relative path | Yes | Relative path to local profile-view JPEG/PNG photo. | Never allowed to be missing. |
| `height_cm` | Float | Centimeters (cm) | Yes | User-reported standing height without footwear. Valid range: `[100.0, 230.0]`. | Never allowed to be missing (primary scale anchor). |
| `weight_kg` | Float | Kilograms (kg) | No | Optional self-reported body weight. Valid range: `[30.0, 200.0]`. | Left blank / empty string if unrecorded. |
| `chest_tape_cm` | Float | Centimeters (cm) | Yes | Ground-truth tape measurement at chest/bust level (Reading 1). | Never allowed to be missing for evaluation. |
| `chest_tape_rep2_cm`| Float | Centimeters (cm) | No | Repeat tape measurement reading for intra-rater variability. | Empty if repeat reading not collected. |
| `waist_tape_cm` | Float | Centimeters (cm) | Yes | Ground-truth tape measurement at natural waist (Reading 1). | Never allowed to be missing for evaluation. |
| `waist_tape_rep2_cm`| Float | Centimeters (cm) | No | Repeat tape measurement reading at natural waist. | Empty if repeat reading not collected. |
| `hip_tape_cm` | Float | Centimeters (cm) | Yes | Ground-truth tape measurement at maximum hip/buttocks projection. | Never allowed to be missing for evaluation. |
| `hip_tape_rep2_cm`  | Float | Centimeters (cm) | No | Repeat tape measurement reading at hip/buttocks. | Empty if repeat reading not collected. |
| `shoulder_width_tape_cm` | Float | Centimeters (cm) | No | Exploratory biacromial shoulder width (bone-to-bone). | Empty if unrecorded. |
| `inseam_tape_cm` | Float | Centimeters (cm) | No | Exploratory inseam length (crotch to ankle). | Empty if unrecorded. |
| `lighting_adequate`| Boolean | `true` / `false` | Yes | Capture quality flag: even illumination without heavy cast shadows. | Defaults to `false` if unverified. |
| `posture_upright` | Boolean | `true` / `false` | Yes | Capture quality flag: upright posture, straight spine, level gaze. | Defaults to `false` if unverified. |
| `feet_visible` | Boolean | `true` / `false` | Yes | Capture quality flag: both feet and floor contact plane visible. | Defaults to `false` if unverified. |
| `clothing_tight` | Boolean | `true` / `false` | Yes | Capture quality flag: form-fitting clothing without loose folds. | Defaults to `false` if unverified. |
| `protocol_version`| String | e.g. `v1.0` | Yes | Protocol specification version under which data was collected. | Required. |
| `consent_given` | Boolean | `true` / `false` | Yes | Documentation that informed consent was obtained. | Must be `true` to process. |
| `retention_agreed`| Boolean | `true` / `false` | Yes | Documentation that retention for the pilot period was agreed. | Must be `true` to retain. |

### Units & Missing Value Policies
- **Units**: All linear dimensions MUST be recorded in **centimeters (cm)** with up to 1 decimal place. Weights MUST be recorded in **kilograms (kg)**.
- **Missing Values**: Missing optional fields must be represented by empty cells (not `NaN`, `0`, `-1`, or placeholder text). Missing required fields will fail schema validation.

---

## 2. Tape Measurement Protocol

Ground truth tape measurements must be taken with a non-stretch flexible tailoring tape (e.g., fiberglass tape) following standardized anthropometric landmarks:

1. **Chest / Bust (`chest_tape_cm`)**:
   - Landmark: Level with the fullest part of the chest / bust (usually nipple line in men, apex of bust in women).
   - Method: Tape wrapped horizontally around the torso under armpits, parallel to the floor. Participant breathes normally; record reading at the end of a normal exhalation without pulling the tape tight enough to indent skin.
2. **Waist (`waist_tape_cm`)**:
   - Landmark: Natural waistline (the narrowest point of the torso between the lower rib cage and iliac crest, typically 2–3 cm above the navel).
   - Method: Tape kept strictly horizontal. Participant stands upright and breathes out naturally (not sucking in stomach). Measure snug against skin/form-fitting clothing without compression.
3. **Hip (`hip_tape_cm`)**:
   - Landmark: Widest circumference around the buttocks / greater trochanters.
   - Method: Participant stands with heels close together (within 10 cm). Tape passed around the greatest posterior projection of buttocks, keeping tape level with floor.
4. **Shoulder Width (`shoulder_width_tape_cm`)** *(Exploratory)*:
   - Landmark: Biacromial breadth across the posterior shoulders from the lateral edge of the left acromion process to the right acromion process.
5. **Inseam (`inseam_tape_cm`)** *(Exploratory)*:
   - Landmark: From the lowest point of the perineum (crotch) along the medial side of the leg down to the medial malleolus (ankle bone) or floor.
6. **Repeat Measurements**:
   - Take 2 independent readings (`rep1` and `rep2`) for chest, waist, and hip to monitor intra-rater measurement variability.

---

## 3. Photo Capture Protocol

Accurate image-based scale calibration and boundary extraction require strict capture consistency:

1. **Camera Position & Height**:
   - Device mounted on a tripod or stable vertical stand.
   - Lens height set to approximately subject waist/mid-torso height (~90–100 cm above floor).
   - Orientation: Vertical portrait mode. Camera must be plumb (0° roll, 0° pitch tilt) to prevent perspective distortion.
2. **Subject Distance & Framing**:
   - Distance: 2.5 to 3.0 meters from the camera lens.
   - Full body must be visible within frame: leave approximately 10–15% vertical headroom above crown of head and ensure feet/floor junction is visible.
3. **Attire**:
   - Close-fitting, non-compressive athletic clothing (e.g., tight sports leggings, compression top, base layers).
   - No baggy shirts, bulky jackets, skirts, or shoes with thick elevated soles (barefoot or socks preferred).
4. **Lighting & Background**:
   - Plain, solid, neutral background (e.g., light-colored blank wall).
   - Diffuse, even lighting from front/top to minimize harsh drop-shadows that distort edge segmentation.
5. **Postures**:
   - **Front View**: Facing camera squarely, standing straight, feet shoulder-width apart, arms slightly abducted (~20–30° from torso) with palms facing thighs so the torso silhouette is clearly separated from arms.
   - **Side (Profile) View**: Rotated 90° clockwise or counter-clockwise facing perpendicular to camera, arms held slightly back or angled so as not to occlude chest, waist, and buttocks outlines.

---

## 4. Privacy, Consent & Data Governance

1. **Data Minimization**:
   - Real participant names, phone numbers, email addresses, and locations must NEVER be stored in tabular datasets or code files.
   - Every subject is assigned a pseudo-random identifier (`P001`, `P002`, etc.).
2. **Local Isolation & Git Rules**:
   - All participant images and actual measurement tables reside in `data/raw/` or `data/participants/`, strictly ignored by `.gitignore`.
   - Never commit participant images or real ground-truth tables into Git.
3. **Informed Consent**:
   - All volunteers must review and sign an informed consent notice explaining that photos and body measurements will only be used locally for algorithm feasibility evaluation.
4. **Retention & Right to Deletion**:
   - Data is retained only for the duration of the feasibility evaluation.
   - Any participant may request deletion at any time; upon request, their raw images and measurement records will be permanently erased within 24 hours.
