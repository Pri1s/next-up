# Feature Specification: Dribble Cycle Metrics Analysis

**Feature Branch**: `001-dribble-cycle-metrics`  
**Created**: 2024-12-29  
**Status**: Draft  
**Input**: User description: "Dribble cycle detection and metrics analysis system for basketball motion analysis"

## Clarifications

### Session 2024-12-29

- Q: What value should the control threshold constant `k` have for `d_thr = k * shoulder_width_session`? → A: k = 0.5 (configurable; may need tuning if contact windows are inconsistent during testing)
- Q: What value should the dominant hand margin threshold `delta` be? → A: delta = 0.1 (10% margin; may need adjustment if dominant hand classification appears inaccurate during testing)
- Q: What defines a "meaningful contact window" for determining start_hand and end_hand? → A: Minimum 3 consecutive frames (filters single-frame noise while capturing genuine contact)

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Analyze Complete Dribbling Session (Priority: P1)

A basketball player records a stationary dribbling session and wants to understand their overall dribbling performance through objective metrics. They upload a video, and the system processes it to extract frame-level motion data, detect individual dribble cycles, compute per-cycle metrics, and summarize the session with aggregate statistics.

**Why this priority**: This is the core value proposition—transforming raw video into actionable biomechanical metrics. Without this capability, no other feature can function.

**Independent Test**: Can be fully tested by processing a single reference video and verifying that the output contains valid cycle boundaries, per-cycle metrics, and session averages. Delivers quantitative dribbling analysis.

**Acceptance Scenarios**:

1. **Given** a video with normalized frame data containing ball and pose landmarks, **When** the system processes the video, **Then** it produces a list of detected dribble cycles with valid start/end boundaries.
2. **Given** detected cycles, **When** per-cycle metrics are computed, **Then** each cycle contains timing metrics (duration), ball height metrics (max, min, avg, range), and contact/control metrics.
3. **Given** all cycle metrics, **When** session-level aggregates are computed, **Then** the output includes mean and variance for key metrics across all cycles.

---

### User Story 2 - Identify Hand Usage Patterns (Priority: P2)

A player wants to understand which hand they predominantly use during dribbling and whether they perform crossover dribbles. The system labels per-frame hand contact, identifies dominant hand per cycle, and detects crossover events.

**Why this priority**: Hand analysis enables targeted training feedback. Players need to know if they favor one hand excessively or if their crossover timing is consistent.

**Independent Test**: Can be tested by analyzing a video with known crossover dribbles and verifying that crossover cycles are correctly identified and hand ratios are computed.

**Acceptance Scenarios**:

1. **Given** a dribble cycle with ball-wrist proximity data, **When** per-frame contact labeling is performed, **Then** each frame is labeled as L (left), R (right), or None (no contact).
2. **Given** a cycle with mixed L and R contact windows, **When** crossover detection runs, **Then** the cycle is marked as `is_crossover=True` with `start_hand` and `end_hand` identified.
3. **Given** all non-crossover cycles, **When** session hand ratios are computed, **Then** the output includes `left_hand_ratio` and `right_hand_ratio` that sum to approximately 1.0.

---

### User Story 3 - Measure Ball Control Quality (Priority: P3)

A player wants to know how well they maintain control of the ball during dribbling. The system computes control deviation metrics that indicate how close the ball stays to the controlling hand.

**Why this priority**: Control quality is a key indicator of dribbling skill. Lower deviation suggests tighter ball handling.

**Independent Test**: Can be tested by comparing control deviation metrics between a skilled and novice dribbling video—skilled should show lower deviation values.

**Acceptance Scenarios**:

1. **Given** a cycle with frames labeled for hand contact, **When** control deviation is computed, **Then** `control_deviation_in_control` reflects the mean ball-to-wrist distance during contact frames.
2. **Given** a session, **When** aggregate control deviation is computed, **Then** the output includes mean and variance of `control_deviation_in_control` across all cycles.

---

### Edge Cases

- What happens when a frame has no valid pose data (None frame)? → The frame is excluded from cycle detection and metric computation; only valid frames are processed.
- What happens when neither wrist is detected in a frame? → The frame is labeled as `unknown` contact and excluded from contact-based metrics.
- What happens when consecutive troughs are too close (noise)? → A minimum dribble duration threshold filters out false cycle boundaries.
- What happens when body_height is too small (< 10 normalized units)? → The frame is marked invalid (None) during normalization.
- What happens when there are large gaps of missing frames? → For now, skip invalid frames and process the remaining valid sequence; segmentation logic is deferred.
- What happens when no cycles are detected? → The session returns zero cycles with appropriate warnings.

## Requirements _(mandatory)_

### Functional Requirements

#### Data Preprocessing

- **FR-001**: System MUST filter out None (invalid) frames before cycle detection, preserving only frames with valid normalized coordinates.
- **FR-002**: System MUST preserve `frame_index` and `timestamp_ms` for all valid frames throughout processing.
- **FR-003**: System MUST handle gaps in frame data by skipping invalid frames without segmentation (for initial implementation).

#### Cycle Detection

- **FR-004**: System MUST detect dribble cycle boundaries using ball vertical position (`ball_y = ball_center[1]`) from normalized frames.
- **FR-005**: System MUST identify bounce points as troughs (local minima) in the `ball_y` signal.
- **FR-006**: System MUST define each cycle as the sequence of frames between two consecutive troughs.
- **FR-007**: System MUST enforce a minimum dribble duration of 10 frames between troughs to filter noise-induced false cycles (configurable via `min_cycle_duration` parameter).
- **FR-008**: System MUST assign a unique `cycle_id` to each valid frame within a detected cycle.

#### Control Threshold Computation

- **FR-009**: System MUST compute per-frame shoulder width as the Euclidean distance between `left_shoulder` and `right_shoulder` (normalized coordinates).
- **FR-010**: System MUST compute a session-level `shoulder_width_session` as the median of all per-frame shoulder widths.
- **FR-011**: System MUST define the control threshold as `d_thr = k * shoulder_width_session` where `k = 0.5` (configurable). _Note: If contact windows appear inconsistent during testing (too many false positives/negatives), adjust `k` accordingly—lower values are stricter, higher values are more lenient._

#### Per-Frame Contact Labeling

- **FR-012**: System MUST compute `d_left` as the Euclidean distance from `ball_center` to `left_wrist` when `left_wrist` is not None.
- **FR-013**: System MUST compute `d_right` as the Euclidean distance from `ball_center` to `right_wrist` when `right_wrist` is not None.
- **FR-014**: System MUST label each frame as:
  - `L` if `d_left < d_thr` and `d_left <= d_right` (or `d_right` unavailable)
  - `R` if `d_right < d_thr` and `d_right < d_left` (or `d_left` unavailable)
  - `None` if both distances >= `d_thr`
  - `unknown` if neither wrist is available
- **FR-015**: System MUST compute `d_min` as the minimum of available wrist distances for each frame.

#### Contact Windows

- **FR-016**: System MUST group consecutive frames with the same hand label (L or R) into contact windows (contact_events).
- **FR-017**: System MUST store for each contact_event: `hand`, `start_frame_index`, `end_frame_index`, `t_start_ms`, `t_end_ms`.
- **FR-018**: System SHOULD compute optional normalized time in cycle (`t_norm_start`, `t_norm_end`) for each contact_event.

#### Cycle-Level Metrics

- **FR-019**: System MUST compute per-cycle timing metrics: `start_time`, `end_time`, `duration`.
- **FR-020**: System MUST compute per-cycle ball height metrics from normalized `ball_y`: `max_height`, `min_height`, `avg_height`, `height_range`.
- **FR-021**: System MUST compute per-cycle contact timing metrics:
  - `contact_time_fraction_left` = (time labeled L) / duration
  - `contact_time_fraction_right` = (time labeled R) / duration
  - `controlled_time_ratio` = (time labeled L or R) / duration
- **FR-022**: System MUST determine per-cycle hand fields:
  - `start_hand`: first meaningful contact window (minimum 3 consecutive frames) near cycle start
  - `end_hand`: last meaningful contact window (minimum 3 consecutive frames) near cycle end
  - `is_crossover`: True if `start_hand != end_hand` (when both known)
  - `dominant_hand`: based on contact fractions with margin threshold `delta = 0.1` (10%, configurable). A hand is dominant if its contact fraction exceeds the other by at least delta. _Note: If dominant hand classification appears inaccurate during testing, adjust delta—lower values are more sensitive, higher values require stronger preference._
- **FR-023**: System SHOULD compute `switch_time_norm` for crossover cycles as the normalized midpoint between end of last start-hand window and start of first end-hand window.
- **FR-024**: System MUST compute per-cycle control deviation metrics:
  - `control_deviation_overall`: mean of `d_min` over all frames with wrists present
  - `control_deviation_in_control`: mean of `d_min` over frames labeled L or R

#### Session-Level Aggregates

- **FR-025**: System MUST compute mean and variance across all cycles for: `duration`, `max_height` (or `avg_height`), `controlled_time_ratio`, `control_deviation_in_control`.
- **FR-026**: System MUST count `crossovers_count` as the number of cycles with `is_crossover == True`.
- **FR-027**: System MUST compute `left_hand_ratio` and `right_hand_ratio` using non-crossover cycles where `dominant_hand` (fallback to `end_hand`) is known, excluding unknown values.

### Key Entities

- **NormalizedFrame**: A single frame with body-relative normalized coordinates. Contains `frame_index`, `timestamp_ms`, `ball_center`, `left_wrist`, `right_wrist`, `left_shoulder`, `right_shoulder`, `left_knee`, `right_knee`, `hip_center`, `body_height`.

- **LabeledFrame**: A NormalizedFrame enriched with `cycle_id`, `contact_label` (L/R/None/unknown), `d_left`, `d_right`, `d_min`.

- **ContactEvent**: A continuous window of frames with the same hand contact. Contains `hand`, `start_frame_index`, `end_frame_index`, `t_start_ms`, `t_end_ms`, optional `t_norm_start`, `t_norm_end`.

- **Cycle**: A complete dribble cycle from trough to trough. Contains `cycle_id`, timing metrics, ball height metrics, contact metrics, hand fields, control deviation metrics, and list of `contact_events`.

- **SessionSummary**: Aggregate statistics across all cycles. Contains means, variances, counts, and ratios as specified in FR-025 through FR-027.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: System correctly identifies cycle boundaries with 95%+ accuracy on reference videos with known dribble counts.
- **SC-002**: Per-cycle metrics (duration, height metrics, contact ratios) are deterministic—identical inputs produce identical outputs.
- **SC-003**: All metrics are traceable to specific frames and cycles; any metric value can be verified by examining underlying frame data.
- **SC-004**: Hand labeling correctly identifies crossover dribbles when ball transfers between hands within a single cycle.
- **SC-005**: Control deviation metrics correlate with observable ball handling tightness—lower values indicate closer ball-wrist proximity during contact.
- **SC-006**: Session aggregates accurately summarize cycle-level data—mean and variance calculations are mathematically correct.
- **SC-007**: System processes a 60-second video (approximately 1800 frames at 30fps) in under 10 seconds on standard hardware.
- **SC-008**: All metrics have clear physical interpretation documented and can be explained in plain language.
