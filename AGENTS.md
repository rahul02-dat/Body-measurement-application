# AGENTS.md --- Photo-Based Body Measurement MVP

## 1. Mission

Build a research-first MVP that evaluates whether two guided smartphone
photographs plus user-provided height can support useful clothing-size
recommendations.

**Primary use case:** recommend a size for one selected brand and
garment category using the brand's published size chart.

**First deliverable:** a reproducible Python feasibility spike evaluated
against tape-measured ground truth. Do not build the mobile app until
the feasibility gate is reviewed.

This is an experimental system. Never present estimated measurements as
exact, clinically validated, or suitable for tailoring unless separate
evidence establishes that claim.

## 2. Non-negotiable operating rules

1.  **Inspect before changing.** Read the existing repository, this
    file, `README.md`, dependency manifests, and tests before editing.
    Preserve working conventions unless they conflict with this file.
2.  **Work in small, verifiable steps.** Implement one phase at a time.
    Run relevant tests after each meaningful change. Report commands run
    and their results.
3.  **Do not skip the feasibility gate.** Do not implement production
    mobile screens, authentication, cloud storage, or a backend before
    the Python baseline has been evaluated and a human approves
    proceeding.
4.  **No fabricated performance.** Do not invent accuracy, confidence,
    sample counts, validation results, or citations. Label targets as
    proposed until measured.
5.  **Keep participants separated in evaluation.** Both photos and all
    measurements from one participant must stay in the same data
    partition.
6.  **No data leakage.** Fit preprocessing, calibration, feature
    selection, and thresholds on training data only. Never tune against
    the final test set.
7.  **Fail safely.** If the person, pose, body boundary, scale, or image
    quality cannot be assessed adequately, return a structured failure
    instead of a plausible-looking number.
8.  **Minimize sensitive data.** Do not commit real participant images,
    identifiable information, secrets, or private measurement datasets.
    Use synthetic fixtures for tests.
9.  **No silent model substitutions.** Record model name, version,
    source URL, license, checksum where practical, and configuration.
    Check current documentation and license terms before adding a
    dependency or model.
10. **Ask before irreversible or costly actions.** Do not delete user
    data, upload photos, create paid cloud resources, or send
    participant data to external services without explicit approval.
11. **Keep claims proportional to evidence.** The product initially
    recommends clothing sizes; it does not estimate body composition,
    provide medical advice, or promise tape-measure accuracy.
12. **Do not add speculative features.** No avatars, automatic learning
    from corrections, multi-brand recommendations, accounts, payments,
    or production backend unless explicitly approved.

## 3. Product scope

### In scope for the feasibility spike

-   A front photograph and a side photograph captured under a documented
    protocol.
-   User-entered height as the initial scale anchor.
-   Pose landmarks and person segmentation.
-   Approximate chest/bust, waist, and hip circumferences as primary
    experimental targets.
-   Shoulder width and inseam as exploratory measurements only.
-   A transparent geometric baseline using front width and side depth at
    corresponding body levels.
-   An ellipse circumference approximation.
-   A CSV of tape measurements and capture metadata.
-   Per-measurement error analysis and size-chart evaluation.
-   Diagnostic overlays and explicit rejection reasons.

### Out of scope until approved

-   A claim that the system produces exact measurements.
-   Tailoring-grade measurements.
-   Fitness or body-fat estimation.
-   Training a new deep-learning model from scratch.
-   Automatic model improvement from user corrections.
-   3D avatar generation or parametric human-body reconstruction.
-   Multi-brand or multi-category sizing.
-   User accounts, payments, analytics SDKs, or production cloud
    services.
-   Uploading images to a third-party service by default.

## 4. Preferred architecture

Start with a Python-only experiment. Do not assume a backend is
necessary.

Suggested initial layout (adapt to an existing repository instead of
overwriting it):

``` text
body-measurement-spike/
├── AGENTS.md
├── README.md
├── requirements.txt or pyproject.toml
├── .gitignore
├── data/
│   ├── README.md
│   └── measurements.example.csv
├── models/
│   └── README.md
├── notebooks/
│   └── feasibility_analysis.ipynb
├── src/
│   └── body_measurement/
│       ├── __init__.py
│       ├── config.py
│       ├── schemas.py
│       ├── image_io.py
│       ├── quality_checks.py
│       ├── pose_detection.py
│       ├── segmentation.py
│       ├── scale_calibration.py
│       ├── measurement_geometry.py
│       ├── sizing.py
│       ├── evaluation.py
│       └── cli.py
└── tests/
    ├── test_schemas.py
    ├── test_geometry.py
    ├── test_scale_calibration.py
    ├── test_sizing.py
    └── test_evaluation.py
```

Preferred tools for the spike:

-   Python version: choose a version supported by all selected
    dependencies and document it.
-   NumPy and OpenCV for image processing and geometry.
-   MediaPipe Pose Landmarker as the first pose-detection candidate;
    evaluate its optional segmentation mask.
-   pandas for tabular data.
-   scikit-learn for later calibration experiments and participant-level
    cross-validation.
-   pytest for automated tests.
-   Matplotlib for diagnostic plots when needed.

Do not pin versions from memory. Check current official documentation
and compatibility before selecting versions. Add only dependencies
actually used.

Official reference:
https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python

## 5. Implementation sequence

### Phase S0-A --- Repository and protocol setup

1.  Inspect the repository and report its current state.
2.  Create or update this project structure without overwriting
    unrelated files.
3.  Write a README describing the goal, limitations, setup, data
    protocol, and commands.
4.  Define exact tape-measure landmarks and measurement instructions
    before collecting data.
5.  Define a photo capture protocol:
    -   same phone/camera where practical;
    -   fixed camera position, height, orientation, and subject
        distance;
    -   full body visible, including feet;
    -   plain background and even lighting;
    -   close-fitting, non-compressive clothing;
    -   consistent upright stance and arm placement;
    -   front and side views captured under the same setup.
6.  Document consent, data minimization, retention, and deletion
    procedures.
7.  Add `.gitignore` rules for raw images, local datasets, model
    binaries where appropriate, virtual environments, secrets, and
    generated outputs.
8.  Create a synthetic/example CSV schema. Never populate it with
    invented measurements presented as real observations.

**Exit criteria:** setup instructions work in a clean environment;
protocol and data schema are documented; no real personal data is
committed.

### Phase S0-B --- Data schema and image loading

Implement validated data structures and safe image loading.

Each participant record should use a random, non-identifying ID and
include at minimum:

-   `participant_id`
-   `front_image_path`
-   `side_image_path`
-   `height_cm`
-   optional `weight_kg`
-   `chest_tape_cm`
-   `waist_tape_cm`
-   `hip_tape_cm`
-   optional `shoulder_width_tape_cm`
-   optional `inseam_tape_cm`
-   repeat tape readings where collected
-   capture-quality flags
-   measurement protocol/version
-   consent and retention status, without names or contact details

Use a documented policy for missing values and units. Do not infer
missing tape measurements. Store identity/contact details separately if
they are needed at all.

**Exit criteria:** malformed rows, invalid units, missing required
fields, and unreadable images produce clear validation errors.

### Phase S0-C --- Pose detection and segmentation

1.  Wrap the chosen pose model behind a small, testable interface.
2.  Run pose detection independently on the front and side image.
3.  Record landmark coordinates and visibility/presence values where
    provided.
4.  Request segmentation masks if supported by the selected model.
5.  Save diagnostic overlays showing landmarks and masks.
6.  Add quality checks for missing/low-quality landmarks, incomplete
    body visibility, multiple people, and obvious occlusion.
7.  Treat pose world coordinates as model outputs, not as verified
    metric body measurements.
8.  Record model asset provenance, version, license, and configuration.

**Exit criteria:** a batch command processes a sample directory and
produces structured outputs plus diagnostic images; failures are
explicit and reproducible.

### Phase S0-D --- Scale calibration

Implement the initial height-based scale estimate, but isolate it in its
own module.

1.  Detect the visible top and bottom of the body silhouette.
2.  Estimate pixels-per-centimeter from entered height and the detected
    body span.
3.  Record which body bounds were used and whether they were reliable.
4.  Reject images where the head or feet are cropped, the person is
    slouching materially, or the scale anchor cannot be determined.
5.  Document that entered height may be inaccurate and that
    perspective/camera tilt can distort scale.
6.  Add experiments that vary camera distance, camera height, and tilt
    to test sensitivity.
7.  Do not claim that a level-phone sensor alone solves perspective or
    scale.

**Exit criteria:** unit tests cover valid scale conversion, invalid
heights, missing bounds, cropped images, and non-finite values; scale
assumptions are visible in reports.

### Phase S0-E --- Geometric baseline

Implement a transparent, deterministic baseline before any learned
calibration.

1.  Define chest/bust, waist, and hip levels using a documented landmark
    mapping.

2.  Extract front-view width and side-view depth at corresponding levels
    from the masks.

3.  Document how the levels are mapped between images and reject
    inconsistent views.

4.  Convert pixel widths/depths to approximate centimeters using the
    scale module.

5.  Approximate each cross-section as an ellipse.

6.  Use Ramanujan's ellipse circumference approximation:

    `a = width_cm / 2`

    `b = depth_cm / 2`

    `C ≈ pi * (3*(a+b) - sqrt((3*a+b)*(a+3*b)))`

7.  Validate inputs: widths and depths must be finite and positive;
    invalid geometry must return a structured failure.

8.  Implement shoulder width and inseam only as exploratory outputs
    after the primary three measurements work.

9.  Add unit tests using synthetic masks and known geometric shapes.

10. Save diagnostic overlays marking each selected cross-section.

Important: the ellipse model is a hypothesis. Real human cross-sections
are not necessarily elliptical, and clothing, posture, segmentation,
perspective, and body-level selection may dominate error. Do not conceal
these limitations.

**Exit criteria:** deterministic geometry tests pass; one image pair can
be processed end-to-end; all estimates can be traced to intermediate
measurements.

### Phase S0-F --- Evaluation and baseline report

1.  Compare estimates with tape measurements from the documented
    protocol.
2.  Compute metrics separately for chest/bust, waist, and hip:
    -   mean absolute error (MAE);
    -   median absolute error;
    -   signed bias;
    -   90th-percentile absolute error;
    -   proportion within predeclared error bands;
    -   processing failure/rejection rate.
3.  Report repeat tape-reading variability and repeat-capture
    variability where available.
4.  Report results by relevant capture-quality and participant subgroups
    when sample size permits.
5.  Produce plots and a machine-readable CSV of per-participant
    predictions and errors.
6.  Record failed cases, not only successful estimates.
7.  Do not present illustrative numbers as results.

**Exit criteria:** a single documented command regenerates the
evaluation report from the input manifest; report includes sample
counts, missing data, exclusions, metrics, and limitations.

### Phase S0-G --- Size-chart evaluation

1.  Select one real brand and one garment category before final
    evaluation.
2.  Obtain and record the source/date for the brand's size chart and its
    measurement conventions.
3.  Encode size boundaries as data, not scattered conditional
    statements.
4.  Define deterministic rules for ties, boundary values, missing
    measurements, and incompatible charts.
5.  Derive a reference size from tape measurements using the same chart
    rules.
6.  Derive a predicted size from image estimates using those rules.
7.  Report:
    -   exact-size accuracy;
    -   adjacent-size accuracy;
    -   confusion matrix by size;
    -   abstention rate;
    -   recommendation coverage.
8.  Do not tune thresholds against the final test participants.

**Exit criteria:** report compares image-based sizing with tape-based
sizing for the same participants and the same size chart.

### Phase S0-H --- Feasibility decision

The initial 20--30 volunteers are a pilot, not proof of generalization.
Use a participant-level split or participant-level cross-validation for
exploratory calibration. Never place one person's front photo in one
partition and their side photo in another.

Provisional targets to discuss before examining results:

-   Aim for MAE of 2 cm or less for chest/bust, waist, and hip.
-   Aim for at least 80% exact-size agreement.
-   Aim for at least 95% agreement within one adjacent size.
-   Track rejection rate and recommendation coverage alongside accuracy.

These are engineering hypotheses, not universal industry standards.
Confirm whether they are appropriate for the selected size chart and
commercial consequences. With a small pilot, uncertainty will be high.

Choose one documented outcome:

-   **Proceed to a larger validation study:** results meet predeclared
    pilot criteria and failure modes appear manageable.
-   **Revise the capture or geometry pipeline:** results miss criteria
    for an identifiable, testable reason.
-   **Stop or change the use case:** performance remains insufficient or
    the approach cannot be validated economically.

Do not start mobile implementation until a human explicitly approves
proceeding after reviewing this report.

### Phase S1 --- Calibration experiment (only after baseline report)

1.  Establish a reproducible uncalibrated baseline.
2.  Train a simple per-measurement linear or Ridge regression only if
    residual analysis indicates systematic bias.
3.  Candidate features may include baseline measurement, entered height,
    and optionally weight. Test each feature's incremental value.
4.  Fit preprocessing and models only on training participants.
5.  Use participant-level cross-validation; reserve a final untouched
    participant test set when data volume permits.
6.  Compare calibrated and uncalibrated metrics on the same held-out
    participants.
7.  Reject calibration if it does not improve held-out performance or
    harms subgroup performance.
8.  Record model version, feature list, training cohort definition, and
    limitations.

Do not implement automatic learning from user corrections. That requires
explicit consent, enough representative data, a governed training
pipeline, and fresh validation.

### Phase S2 --- Mobile MVP (only after approval)

Preferred default: Flutter if the project owner has no established
framework preference. React Native is also acceptable if the owner
already knows it well. Do not build both.

Implement only:

1.  A start/details screen with height and units.
2.  Guided front-photo capture.
3.  Guided side-photo capture.
4.  Capture checks and retake flow.
5.  Processing/loading and explicit error states.
6.  Results screen with validated measurements and size recommendation.
7.  Manual correction of displayed values, clearly distinguished from
    model estimates.
8.  Save/export only if needed for the pilot; otherwise keep data in
    memory or local storage.
9.  Clear deletion and privacy controls.

Use the same measurement definitions and test vectors as the Python
prototype. Add regression tests to ensure the mobile implementation does
not silently diverge from the validated reference engine. Prefer
on-device processing where practical.

Do not add accounts, cloud sync, payment, analytics, avatars, or a
backend unless the pilot requires them and the owner approves.

### Phase S3 --- Pilot and retailer trial

1.  Validate with participants not used to tune the model.
2.  Include variation in body shape, clothing fit, height, and capture
    conditions.
3.  Document inclusion/exclusion rules and report failures.
4.  Obtain explicit informed consent before retaining photos or using
    data for model improvement.
5.  Test sizing performance with one retailer or a controlled
    representative workflow.
6.  Agree on success criteria with the retailer before the trial.
7.  Revisit thresholds and claims only after analysis, not to
    retroactively declare success.

## 6. Data format and privacy rules

-   Raw photos and real participant CSVs must remain outside version
    control by default.
-   Include only synthetic examples in the repository.
-   Do not log image bytes, full local paths containing personal names,
    or sensitive measurement records.
-   Use random participant IDs. Do not place names, phone numbers, email
    addresses, or addresses in analysis files.
-   Make retention and deletion behavior explicit and testable.
-   If images leave the device, document destination, purpose, retention
    period, access controls, and consent before implementing upload.
-   Do not use participant images to train or improve models without
    specific, informed permission.
-   Review applicable privacy obligations for each launch jurisdiction.
    For India, verify the DPDP Act and Rules provisions and commencement
    dates currently in force with qualified counsel before a public
    pilot or release.
-   Never claim legal compliance merely because images are processed
    locally or deleted.

## 7. Engineering standards

-   Use type hints for public functions.
-   Keep modules focused and avoid oversized notebooks as the only
    implementation.
-   Put tunable thresholds in a configuration file with units and
    explanations.
-   Use deterministic functions for geometry and sizing.
-   Validate external inputs and handle exceptions with actionable
    messages.
-   Do not swallow exceptions or return fabricated defaults.
-   Separate model inference, geometry, calibration, sizing, and
    evaluation.
-   Keep diagnostic artifacts reproducible and avoid overwriting source
    data.
-   Add tests for normal, boundary, invalid, and failure cases.
-   Use comments to explain assumptions and non-obvious decisions, not
    to narrate every line.
-   Update README and dependency manifests when setup or behavior
    changes.
-   Avoid premature abstractions and unrelated refactors.

## 8. Testing requirements

At minimum, tests must cover:

-   Input schema and unit validation.
-   Image read failures and unsupported/corrupt files.
-   Missing landmarks and low-quality segmentation.
-   Cropped bodies and multiple-person cases where detectable.
-   Scale conversion and invalid scale anchors.
-   Ellipse circumference calculations, including circle and invalid
    inputs.
-   Cross-section selection and mask-boundary edge cases.
-   Size-chart boundary/tie behavior.
-   Metric calculations on known synthetic examples.
-   Participant-level data splitting.
-   Calibration leakage prevention.
-   Structured rejection behavior and report generation.

Do not require real participant photos in automated tests. Use synthetic
masks, generated fixtures, or legally approved test assets.

## 9. Documentation and deliverables

Every phase should leave these artifacts where applicable:

-   Updated README and exact setup/run/test commands.
-   Configuration and model provenance.
-   Capture and tape-measure protocol.
-   Data dictionary and example CSV.
-   Diagnostic overlays and reproducible output files.
-   Evaluation report with sample counts, errors, exclusions, and
    limitations.
-   Decision record explaining proceed/revise/stop and why.

When finishing a task, report:

1.  What changed.
2.  Files added or modified.
3.  Commands and tests run, with pass/fail results.
4.  Known limitations and unverified assumptions.
5.  The next smallest recommended task.
6.  Whether the current phase's exit criteria are met.

## 10. Coding-agent workflow

At the start of each session:

1.  Read this file and the relevant project documentation.
2.  Inspect `git status` and avoid overwriting unrelated user changes.
3.  Identify the current phase and its exit criteria.
4.  State a concise plan before substantial edits.
5.  Implement only the smallest useful increment.
6.  Run relevant tests and inspect generated artifacts.
7.  Summarize evidence, limitations, and next step.

If an instruction conflicts with existing repository constraints or the
task cannot proceed safely, explain the conflict and ask one focused
question rather than guessing.

## 11. Current first task

Begin with **Phase S0-A only**:

-   Inspect the repository.
-   Report the current files, language/runtime, and existing tests.
-   Propose the minimal changes needed to establish the Python
    feasibility spike.
-   Do not build the mobile app, install unnecessary dependencies,
    download model weights, or process real personal photos yet.
-   If the repository is empty, create the minimal Python project
    skeleton, README, data protocol outline, example CSV schema, and
    `.gitignore`.
-   Verify the setup and report the next task.

## 12. Official references to verify during implementation

-   AGENTS.md convention: https://agents.md/
-   MediaPipe Pose Landmarker for Python:
    https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python
-   MediaPipe Pose Landmarker overview:
    https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker
-   India DPDP Act/Rules information: https://www.meity.gov.in/ and
    https://www.pib.gov.in/

Check current documentation, supported platforms, package compatibility,
model terms, and legal commencement information at implementation time.
Do not assume links or API behavior remain unchanged.
