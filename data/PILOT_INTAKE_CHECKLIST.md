# Pilot Volunteer Data Collection Intake Checklist

This checklist guides the collection of physical ground truth tape measurements and photograph capture for the **20–30 volunteer pilot study** in accordance with [AGENTS.md](file:///Users/rahulmac/Documents/Projects/Body-Measurement-App/AGENTS.md) and [data/README.md](file:///Users/rahulmac/Documents/Projects/Body-Measurement-App/data/README.md).

---

## 1. Pre-Session Consent & Privacy Anonymization

- [ ] **Assign Random Pseudonym:** Assign a non-identifying identifier (e.g. `P_001`, `P_002`, `PILOT_010`).
  > **Rule:** Never record the volunteer's real name, email, phone number, or biometric identifier in the manifest or image filename.
- [ ] **Informed Consent Verified:** Explain that two full-body photos and tape measurements will be processed **strictly locally on device** to evaluate clothing-size recommendations.
- [ ] **Data Retention Option:** Confirm whether the participant permits local image retention for evaluation (`retention_agreed=True` / `False`).

---

## 2. Capture Environment & Equipment Setup

- [ ] **Lighting:** Even, diffuse front/ambient lighting. Avoid harsh backlights, strong shadows, or direct windows behind the subject.
- [ ] **Background:** Plain, neutral wall with strong color contrast against the participant's clothing.
- [ ] **Camera Device:** Same smartphone camera across both views.
- [ ] **Mounting & Height:** Smartphone mounted firmly on a tripod or stable surface at **mid-torso height (~90–100 cm above floor)**.
- [ ] **Orientation & Tilt:** Portrait orientation, **0° level pitch** (no downward or upward tilt).
- [ ] **Distance:** Fixed distance of **2.5 to 3.0 meters** from the subject.

---

## 3. Participant Attire & Stance Protocol

- [ ] **Clothing:** Close-fitting athletic clothing (e.g. compression shirt / sports top, leggings / tight athletic shorts).
  > **Note:** Loose shirts, hoodies, thick sweaters, baggy jeans, or skirts are excluded.
- [ ] **Footwear:** Barefoot or socks only. No thick-soled shoes, platform sneakers, or heels.
- [ ] **Framing:** Full body clearly visible in the frame, with ~10–15 cm margin above the head and feet touching the floor clearly visible.

---

## 4. Photo Capture Procedure

### Front Photo (`data/raw/<pid>_front.jpg`):
- [ ] Volunteer faces camera squarely with neutral upright standing posture.
- [ ] Heels together or slightly separated (~5–10 cm).
- [ ] Arms held away from torso at a **20°–30° angle** with open hands (ensures torso contour is not occluded by arms).
- [ ] Capture image and verify framing (no cropped head or feet).

### Side / Profile Photo (`data/raw/<pid>_side.jpg`):
- [ ] Volunteer turns 90° into a true profile view.
- [ ] Same upright posture without shifting position away from camera line.
- [ ] Arms positioned slightly back or forward so the profile outline of the bust, abdomen, and buttocks is unobstructed.
- [ ] Capture image under identical zoom, height, and lighting.

---

## 5. Physical Tape Measurement Protocol

Use a flexible, non-elastic fiberglass anthropometric measuring tape held horizontally:

- [ ] **Height (cm):** Measured barefoot against a vertical flat wall/stadiometer (`height_cm`).
- [ ] **Weight (kg) (Optional):** Measured on calibrated floor scale (`weight_kg`).
- [ ] **Chest / Bust (cm):**
  - Tape placed horizontally around the fullest part of the chest/bust.
  - Measured during normal, relaxed respiration.
  - **Reading 1:** `chest_tape_cm`
  - **Repeat Reading 2:** `chest_tape_rep2_cm`
- [ ] **Waist (cm):**
  - Tape placed horizontally at the natural waist constriction (~2–3 cm above navel).
  - Measured at the end of normal exhalation.
  - **Reading 1:** `waist_tape_cm`
  - **Repeat Reading 2:** `waist_tape_rep2_cm`
- [ ] **Hip (cm):**
  - Tape placed horizontally around the maximum posterior protrusion of the buttocks with heels together.
  - **Reading 1:** `hip_tape_cm`
  - **Repeat Reading 2:** `hip_tape_rep2_cm`

---

## 6. Manifest Entry & Verification

Append the session record to your local pilot CSV manifest (e.g. `data/measurements.pilot.csv`):

```csv
participant_id,front_image_path,side_image_path,height_cm,weight_kg,chest_tape_cm,chest_tape_rep2_cm,waist_tape_cm,waist_tape_rep2_cm,hip_tape_cm,hip_tape_rep2_cm,lighting_adequate,posture_upright,feet_visible,clothing_tight,protocol_version,consent_given,retention_agreed
P_001,data/raw/P_001_front.jpg,data/raw/P_001_side.jpg,175.2,71.0,96.0,96.2,81.5,81.3,98.0,98.0,true,true,true,true,v1.0,true,true
```

Run manifest validation before evaluating:
```bash
python -m body_measurement.cli --validate-manifest data/measurements.pilot.csv
```
