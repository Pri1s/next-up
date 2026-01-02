# Research: Dribble Cycle Metrics Analysis

**Feature Branch**: `001-dribble-cycle-metrics`  
**Date**: 2024-12-29

## Overview

This document consolidates research findings and technical decisions for the dribble cycle metrics feature. All NEEDS CLARIFICATION items from the specification have been resolved during the clarification phase.

---

## 1. Cycle Detection Approach

### Decision

Use **trough detection** (local minima) on normalized `ball_y` signal to identify bounce points as cycle boundaries.

### Rationale

- The ball's lowest point (trough) corresponds to the bounce moment—the most consistent physical marker in a dribble cycle
- Existing `CycleDetector` uses peak detection; switching to trough detection aligns with the spec's definition
- SciPy's `find_peaks` with inverted signal (`-ball_y`) or `argrelmin` can detect troughs

### Alternatives Considered

| Alternative           | Why Rejected                                                                        |
| --------------------- | ----------------------------------------------------------------------------------- |
| Peak detection (apex) | Current implementation uses this, but bounces (troughs) are more physically defined |
| Zero-crossing         | Less robust to noise; doesn't correspond to physical events                         |
| Velocity-based        | Requires derivative computation; more sensitive to noise                            |

### Implementation Note

Modify existing `CycleDetector.detect_cycles()` to use troughs instead of peaks, or add a `use_troughs=True` parameter for backward compatibility.

---

## 2. Control Threshold Computation

### Decision

Compute `d_thr = k * shoulder_width_session` where:

- `k = 0.5` (configurable)
- `shoulder_width_session` = median of per-frame shoulder widths

### Rationale

- Shoulder width provides a stable body-relative reference that scales with player size
- Median is robust to outliers from pose detection errors
- k = 0.5 means ball must be within half a shoulder-width of the wrist to count as "in control"
- All values in normalized (body-height) units, ensuring consistency

### Alternatives Considered

| Alternative           | Why Rejected                                                     |
| --------------------- | ---------------------------------------------------------------- |
| Fixed pixel threshold | Not scale-invariant; violates normalization principle            |
| Torso length          | Less stable than shoulder width due to hip detection variability |
| Per-frame threshold   | Too variable; session-level median provides stability            |

---

## 3. Contact Window Definition

### Decision

A "meaningful" contact window requires **minimum 3 consecutive frames** with the same hand label (L or R).

### Rationale

- At 30fps, 3 frames ≈ 100ms, which filters single-frame noise
- Brief touches (1-2 frames) are often detection artifacts
- 3 frames captures genuine contact while being permissive enough for fast dribbles

### Alternatives Considered

| Alternative     | Why Rejected                                                           |
| --------------- | ---------------------------------------------------------------------- |
| 1-2 frames      | Too permissive; includes noise                                         |
| 5+ frames       | Too strict; may miss quick touches                                     |
| Time-based (ms) | Frame count is simpler and consistent with min_cycle_duration approach |

---

## 4. Dominant Hand Classification

### Decision

A hand is declared dominant if its contact fraction exceeds the other by at least `delta = 0.1` (10%).

### Rationale

- Prevents labeling a hand as dominant when usage is nearly equal (e.g., 52% vs 48%)
- 10% margin provides clear preference signal
- If neither hand exceeds delta, dominant_hand = None (ambiguous)

### Alternatives Considered

| Alternative     | Why Rejected                                              |
| --------------- | --------------------------------------------------------- |
| Simple majority | Too sensitive to small differences                        |
| 20% margin      | Too conservative; many cycles would have no dominant hand |
| Time-weighted   | More complex; simple fraction comparison is sufficient    |

---

## 5. Height Metric Interpretation

### Decision

Use normalized `ball_y` directly where:

- **Smaller values** = higher ball position (closer to head/chest)
- **Larger values** = lower ball position (closer to ground)
- `max_height` = minimum `ball_y` in cycle (highest point)
- `min_height` = maximum `ball_y` in cycle (lowest point, bounce)

### Rationale

- Consistent with image coordinate system (y increases downward)
- Normalization places hip at (0,0); negative y = above hip, positive y = below hip
- No need to invert; document the convention clearly

### Implementation Note

In the `Cycle` data model, store raw `ball_y` values. The naming (`max_height`, `min_height`) refers to physical height, not coordinate values.

---

## 6. Missing Frame Handling

### Decision

Skip None frames during processing; do not segment on gaps (for initial implementation).

### Rationale

- Simplifies implementation; gaps are treated as missing samples
- Cycle detection operates on valid frames only
- Future enhancement: add gap-based segmentation if missing data is frequent

### Alternatives Considered

| Alternative                | Why Rejected                                                                    |
| -------------------------- | ------------------------------------------------------------------------------- |
| Interpolation              | Risks introducing artificial data; violates "metrics must be derived" principle |
| Segmentation on large gaps | Adds complexity; deferred to future iteration                                   |

---

## 7. Data Structure Design

### Decision

Use Python `dataclass` for all entities: `LabeledFrame`, `ContactEvent`, `Cycle`, `SessionSummary`.

### Rationale

- Type hints provide documentation and IDE support
- `dataclass` reduces boilerplate for simple data containers
- Immutable by default with `frozen=True` option
- Easy serialization to dict for future JSON export

### Implementation Note

Place all dataclasses in `src/models/` directory for clear separation from processors.

---

## Dependencies

### Existing (no changes)

- `scipy.signal.find_peaks` — cycle boundary detection
- `numpy` — numerical operations
- `opencv-python` — video processing (Perception layer only)
- `mediapipe` — pose detection (Perception layer only)

### New

- `statistics.median` — shoulder width session computation (stdlib)
- `math.dist` or `numpy.linalg.norm` — Euclidean distance for contact labeling

No new external dependencies required.

---

## Configuration Constants

Add to `src/config.py`:

```python
# Control threshold
contact_threshold_k: float = 0.5  # d_thr = k * shoulder_width_session

# Dominant hand margin
dominant_hand_delta: float = 0.1  # 10% margin to declare dominance

# Meaningful contact window
min_contact_window_frames: int = 3  # minimum consecutive frames for valid contact
```

---

## Open Questions (Deferred)

1. **Visualization**: Should contact labels be visualized on frames? (Deferred to separate feature)
2. **Export format**: JSON/CSV export of metrics? (Deferred to separate feature)
3. **Gap segmentation**: When should large gaps split analysis into segments? (Deferred; skip gaps for now)
