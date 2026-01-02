## Purpose

This application analyzes basketball motion from video, extracts objective biomechanical metrics, and delivers actionable, personalized feedback. It prioritizes:

- correctness over cleverness
- interpretability over opaque intelligence
- scalability over one-off features

## Core Architectural Principles

### 1. Separation of Responsibilities

- Perception: Converts raw video into structured frame-level motion data. Includes frame extraction, pose detection, and ball tracking. Produces no judgments or interpretations.
- Evaluation: Converts motion data into metrics and comparisons. Includes normalization, cycle detection, and statistical aggregation. Must be deterministic and reproducible.
- Interpretation: Converts metrics into human-readable feedback. May involve AI models. Must not compute metrics or infer facts not explicitly provided by Evaluation.
- No layer may assume responsibilities belonging to another.

### 2. Frame-Level Data Is the Source of Truth

- All higher-level constructs (cycles, metrics, averages) must be derived from frame-level data.
- Frame-level data must be preserved internally for debugging, validation, and future features.
- No session-level or cycle-level metric may be computed without a clear derivation from frames.

### 3. Temporal Information Must Be Preserved

- Motion is time-based; analysis must not collapse temporal structure prematurely.
- The required order of processing is strictly:
  1.  Frames
  2.  Cycles (or segments)
  3.  Session-level aggregates
- Skipping or collapsing steps is disallowed.

### 4. Normalization Is Mandatory

- Image-space normalization: joint coordinates must be normalized relative to frame dimensions.
- Body-relative normalization: joint and ball positions must be expressed relative to hip center; measurements must be scaled by body height or an equivalent body-based reference.
- Raw pixel values must never be used for metric computation.

### 5. Cycles Represent Atomic Motion Units

- A “cycle” is the smallest meaningful repeatable motion unit for a given mode.
- For stationary dribbling, one cycle corresponds to one complete dribble.
- Cycles must be detected algorithmically, respect physical constraints (minimum duration, realistic timing), and contain all frames between well-defined boundaries.
- Future modes may redefine what a cycle represents, but the abstraction must remain.

### 6. Metrics Must Be Explainable

- Every metric must have a clear physical or biomechanical meaning.
- It must be explainable in plain language.
- It must be traceable back to specific frames or cycles.
- It must be comparable across sessions and users under controlled conditions.
- Metrics that cannot be explained or justified are invalid.

### 7. Aggregates Are Summaries, Not Replacements

- Session-level averages and summaries exist to summarize performance.
- They must not replace cycle-level analysis, temporal patterns, or variability information.
- Any feedback generated from aggregates must remain consistent with underlying cycle data.

### 8. AI Is an Interpreter, Not an Analyst

- If AI is used, it may only explain metrics, relate them to user goals, and suggest adjustments strictly based on provided data.
- It must not analyze raw video, infer motion patterns independently, or create metrics or conclusions not present in structured input.
- All AI input must be explicitly constructed and constrained.

### 9. Controlled Recording Assumptions Must Be Explicit

- For stationary dribbling:
  - A fixed, front-facing camera
  - A stationary player
  - Minimal lateral movement
- Reference data must be collected under the same conditions.
- Metrics are only valid within these constraints; if assumptions change, evaluation logic must change accordingly.

### 10. Scalability Is a First-Class Requirement

- New modes can be added without rewriting the core pipeline.
- New metrics can be introduced without breaking existing ones.
- New motion segmentation strategies can coexist with cycle-based analysis.
- The pipeline—frames → segments/cycles → metrics → comparison → feedback—must remain intact across all features.

## Non-Negotiable Invariants

- Frame data precedes all interpretation.
- Metrics must be derived, not guessed.
- AI cannot be a source of truth.
- Motion analysis must be reproducible.
- The system must favor correctness over speed.

## Layer Responsibilities

### Perception (input → structured frames)

- Extract frames with timestamps.
- Detect pose landmarks and ball presence/position.
- Track the ball and capture per-frame motion data.
- Do not compute metrics, cycles, or judgments.

### Evaluation (frames → cycles → metrics → aggregates)

- Clean data deterministically (e.g., velocity-based outlier handling).
- Normalize coordinates (hip-centered, body-height scaled; image-space normalized).
- Detect cycles/segments respecting physical timing constraints.
- Compute explainable, deterministic metrics per cycle.
- Produce session-level aggregates that summarize but never replace cycle analyses.

### Interpretation (metrics → feedback)

- Translate metrics and patterns into clear, actionable guidance.
- Constrain any AI so it does not invent data, metrics, or facts.
- Provide confidence and provenance back to cycles and frames.W

## Data & Normalization Contracts

Frame-level record must minimally include:

- frame_index, timestamp_ms
- ball_center (image-space or normalized), hip_center
- key joints required for normalization (e.g., shoulders, hips)

Normalization rules:

- Origin: Hip center → (0, 0)
- Scale: Divide spatial measures by body height (distance from hip center to shoulder center or equivalent)
- Image-space normalization: store coordinates relative to frame dimensions

Raw pixel-space values are never used directly for metrics.

## Cycle Definition (Stationary Dribbling)

- Atomic unit: one complete dribble (ball apex → descent → floor proximity → ascent → apex).

Detection requirements:

- Use monotonic and peak-prominence constraints consistent with minimum cycle duration.
- Include all frames from one cycle’s boundary to the next.
- Skip cycles if insufficient valid normalized frames exist.

## Metrics Rules (Explainability First)

Each metric must include:

- Name and plain-language meaning
- Units or unitless scaling
- Derivation steps from normalized frames (cycle-level provenance)
- Assumptions and constraints (e.g., stationary mode)

Examples (non-exhaustive):

- Cycle duration (ms): time between cycle boundary frames
- Apex height (unitless): smallest normalized y; higher apex implies better ball height control
- Floor proximity (unitless): largest normalized y during cycle
- Vertical range (unitless): floor_y − apex_y
- Stability indicators: population std-dev of y across the cycle

Metrics must be deterministic and reproducible given the same input frames.

## Aggregates Policy

- Aggregates summarize cycle metrics (e.g., mean, std) across the session.
- Aggregates must never contradict cycle-level findings and must point back to the underlying cycles.
- Aggregates do not override cycle variability; feedback must reflect variance and patterns.

## AI Constraints (Interpreter-Only)

AI must only:

- Explain metrics
- Connect metrics to user goals
- Suggest adjustments strictly based on provided metrics

AI must never:

- Process raw video
- Generate new metrics
- Infer hidden facts

All AI prompts must be tightly scoped to existing metrics and constraints.

## Controlled Recording Assumptions (Stationary Mode)

- Fixed, front-facing camera placement
- Player remains largely stationary (minimal lateral movement)
- Reference data gathered under identical conditions
- If these assumptions are violated, the analysis must be flagged as out-of-scope or re-normalized accordingly.

## Scalability & Extensibility

### New modes

- Must define their atomic cycle units and detection criteria
- Must preserve the frames → cycles → metrics → aggregates pipeline

### New metrics

- Must meet explainability and derivation standards
- Must not break existing metrics or require pipeline rework

### New segmentation strategies

- May coexist alongside cycle-based analysis
- Must retain provenance to frames

## Governance & Change Management

- Version the constitution; record changes with rationale and impact.
- Validate changes against invariants and core principles.
- Any change to assumptions or modes must include updated evaluation rules and tests.

## Compliance Checklist

- Perception outputs only structured frames; no metrics.
- Frame records include timestamps and normalization-relevant joints.
- Normalization: hip-centered, body-height scaled; image-space normalized.
- Cycles detected deterministically with physical constraints.
- Metrics computed per cycle; each is explainable and traceable.
- Aggregates used only as summaries; variability preserved.
- AI components, if present, are interpreter-only.
- Controlled assumptions documented and checked.
- Artifacts retained for reproducibility (frame-level provenance).

## Glossary

- Frame-level data: structured per-frame records of detected positions with timestamps.
- Normalized coordinates: hip-centered, body-height scaled positions; optionally frame-dimension normalized.
- Cycle: atomic, repeatable motion unit (one complete dribble in stationary mode).
- Aggregates: session-level summaries of cycle metrics (e.g., means, std dev).
