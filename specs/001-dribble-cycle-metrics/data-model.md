# Data Model: Dribble Cycle Metrics Analysis

**Feature Branch**: `001-dribble-cycle-metrics`  
**Date**: 2024-12-29

## Overview

This document defines the data structures used in the dribble cycle metrics pipeline. All entities flow from frame-level data through cycles to session aggregates, respecting the constitution's temporal hierarchy.

---

## Entity Relationship Diagram

```
┌─────────────────────┐
│  NormalizedFrame    │ (existing, from normalizer.py)
│  - frame_index      │
│  - timestamp_ms     │
│  - ball_center      │
│  - left_wrist       │
│  - right_wrist      │
│  - left_shoulder    │
│  - right_shoulder   │
│  - ...              │
└─────────┬───────────┘
          │ enriched with contact info
          ▼
┌─────────────────────┐
│   LabeledFrame      │ (new)
│  - frame_index      │
│  - timestamp_ms     │
│  - cycle_id         │
│  - contact_label    │
│  - d_left           │
│  - d_right          │
│  - d_min            │
│  - (all normalized  │
│     fields)         │
└─────────┬───────────┘
          │ grouped by consecutive labels
          ▼
┌─────────────────────┐
│   ContactEvent      │ (new)
│  - hand             │
│  - start_frame_idx  │
│  - end_frame_idx    │
│  - t_start_ms       │
│  - t_end_ms         │
│  - t_norm_start     │
│  - t_norm_end       │
└─────────┬───────────┘
          │ aggregated per cycle
          ▼
┌─────────────────────┐
│      Cycle          │ (new)
│  - cycle_id         │
│  - frames[]         │
│  - contact_events[] │
│  - timing_metrics   │
│  - height_metrics   │
│  - contact_metrics  │
│  - hand_fields      │
│  - control_metrics  │
└─────────┬───────────┘
          │ aggregated across session
          ▼
┌─────────────────────┐
│  SessionSummary     │ (new)
│  - cycles[]         │
│  - duration_stats   │
│  - height_stats     │
│  - control_stats    │
│  - hand_ratios      │
│  - crossover_count  │
└─────────────────────┘
```

---

## Entity Definitions

### 1. LabeledFrame

A normalized frame enriched with contact labeling information.

```python
@dataclass
class LabeledFrame:
    """A normalized frame with contact labeling."""

    # Identity
    frame_index: int          # Original frame number in video
    timestamp_ms: float       # Timestamp in milliseconds
    cycle_id: Optional[int]   # Assigned cycle (None if outside cycles)

    # Contact labeling
    contact_label: str        # 'L', 'R', 'None', or 'unknown'
    d_left: Optional[float]   # Distance to left wrist (normalized)
    d_right: Optional[float]  # Distance to right wrist (normalized)
    d_min: Optional[float]    # min(d_left, d_right) when available

    # Normalized positions (from NormalizedFrame)
    ball_center: Optional[tuple[float, float]]
    left_wrist: Optional[tuple[float, float]]
    right_wrist: Optional[tuple[float, float]]
    left_shoulder: Optional[tuple[float, float]]
    right_shoulder: Optional[tuple[float, float]]
    hip_center: tuple[float, float]  # Always (0.0, 0.0)
```

**Validation Rules:**

- `frame_index` >= 0
- `timestamp_ms` >= 0
- `contact_label` must be one of: 'L', 'R', 'None', 'unknown'
- `d_left`, `d_right`, `d_min` >= 0 when present

**Derivation:**

- Created by `ContactLabeler` from `NormalizedFrame`
- `cycle_id` assigned after cycle detection

---

### 2. ContactEvent

A continuous window of frames with the same hand contact.

```python
@dataclass
class ContactEvent:
    """A continuous window of same-hand contact."""

    # Identity
    hand: str                 # 'L' or 'R'

    # Frame boundaries
    start_frame_index: int    # First frame of contact window
    end_frame_index: int      # Last frame of contact window (inclusive)

    # Time boundaries (absolute)
    t_start_ms: float         # Start timestamp in ms
    t_end_ms: float           # End timestamp in ms

    # Time boundaries (normalized to cycle, optional)
    t_norm_start: Optional[float]  # 0.0 to 1.0, position in cycle
    t_norm_end: Optional[float]    # 0.0 to 1.0, position in cycle

    @property
    def duration_ms(self) -> float:
        """Duration of contact window in milliseconds."""
        return self.t_end_ms - self.t_start_ms

    @property
    def frame_count(self) -> int:
        """Number of frames in this contact window."""
        return self.end_frame_index - self.start_frame_index + 1
```

**Validation Rules:**

- `hand` must be 'L' or 'R'
- `start_frame_index` <= `end_frame_index`
- `t_start_ms` <= `t_end_ms`
- `frame_count` >= 3 (minimum meaningful contact window)

**Derivation:**

- Created by grouping consecutive `LabeledFrame` entries with same `contact_label`
- Normalized times computed relative to parent cycle's start/end

---

### 3. Cycle

A complete dribble cycle with all computed metrics.

```python
@dataclass
class Cycle:
    """A complete dribble cycle with metrics."""

    # Identity
    cycle_id: int

    # Frame data (for traceability)
    frames: list[LabeledFrame]
    contact_events: list[ContactEvent]

    # Timing metrics (FR-019)
    start_time_ms: float
    end_time_ms: float
    duration_ms: float

    # Ball height metrics (FR-020)
    max_height: float         # Minimum ball_y (highest position)
    min_height: float         # Maximum ball_y (lowest position, bounce)
    avg_height: float         # Mean ball_y across cycle
    height_range: float       # min_height - max_height

    # Contact timing metrics (FR-021)
    contact_time_fraction_left: float   # [0, 1]
    contact_time_fraction_right: float  # [0, 1]
    controlled_time_ratio: float        # [0, 1]

    # Hand fields (FR-022)
    start_hand: Optional[str]     # 'L', 'R', or None
    end_hand: Optional[str]       # 'L', 'R', or None
    is_crossover: Optional[bool]  # True if start_hand != end_hand
    dominant_hand: Optional[str]  # 'L', 'R', or None (ambiguous)

    # Crossover timing (FR-023)
    switch_time_norm: Optional[float]  # [0, 1] if crossover

    # Control deviation metrics (FR-024)
    control_deviation_overall: Optional[float]
    control_deviation_in_control: Optional[float]
```

**Validation Rules:**

- `cycle_id` >= 0
- `frames` not empty
- `duration_ms` > 0
- `0 <= contact_time_fraction_left <= 1`
- `0 <= contact_time_fraction_right <= 1`
- `0 <= controlled_time_ratio <= 1`
- `contact_time_fraction_left + contact_time_fraction_right <= 1` (remainder is 'None'/'unknown')

**Derivation:**

- Created by `CycleMetrics` processor from list of `LabeledFrame`
- All metrics computed from frame-level data within cycle boundaries

---

### 4. SessionSummary

Aggregate statistics across all cycles in a session.

```python
@dataclass
class SessionSummary:
    """Session-level aggregate statistics."""

    # Source data (for traceability)
    cycles: list[Cycle]
    total_frames: int
    valid_frames: int

    # Duration statistics (FR-025)
    duration_mean: float
    duration_variance: float

    # Height statistics (FR-025)
    max_height_mean: float      # or avg_height_mean
    max_height_variance: float

    # Control statistics (FR-025)
    controlled_time_ratio_mean: float
    controlled_time_ratio_variance: float
    control_deviation_mean: float
    control_deviation_variance: float

    # Crossover count (FR-026)
    crossovers_count: int

    # Hand ratios (FR-027)
    left_hand_ratio: float      # [0, 1]
    right_hand_ratio: float     # [0, 1]
    hand_ratio_sample_size: int # cycles used for ratio calculation

    # Metadata
    shoulder_width_session: float  # Used for d_thr computation
    d_thr: float                   # Control threshold used
```

**Validation Rules:**

- `cycles` may be empty (if no cycles detected)
- `left_hand_ratio + right_hand_ratio ≈ 1.0` (within floating-point tolerance)
- `crossovers_count <= len(cycles)`
- All variance values >= 0

**Derivation:**

- Created by `SessionAggregator` from list of `Cycle`
- Hand ratios computed from non-crossover cycles only
- Statistics exclude cycles with missing values for that metric

---

## State Transitions

### Frame Processing State

```
Raw Frame Data (from Perception)
    │
    ▼ [CoordinateNormalizer]
NormalizedFrame (or None if invalid)
    │
    ▼ [CycleDetector]
NormalizedFrame with cycle boundaries
    │
    ▼ [ContactLabeler]
LabeledFrame (contact_label, distances assigned)
    │
    ▼ [grouped by cycle_id]
List[LabeledFrame] per cycle
    │
    ▼ [CycleMetrics]
Cycle (all metrics computed)
    │
    ▼ [SessionAggregator]
SessionSummary
```

### Contact Label States

```
Frame without wrists ──────────────► 'unknown'
                                         │
Frame with wrists                        │
    │                                    │
    ├── d_min >= d_thr ──────────────► 'None'
    │                                    │
    └── d_min < d_thr                    │
           │                             │
           ├── d_left <= d_right ────► 'L'
           │                             │
           └── d_right < d_left ─────► 'R'
```

---

## Glossary

| Term                     | Definition                                               |
| ------------------------ | -------------------------------------------------------- |
| `d_thr`                  | Control threshold distance; `k * shoulder_width_session` |
| `d_min`                  | Minimum of d_left and d_right for a frame                |
| `shoulder_width_session` | Median shoulder width across all valid frames            |
| `contact_time_fraction`  | Proportion of cycle duration with hand contact           |
| `controlled_time_ratio`  | Proportion of cycle duration with any hand contact       |
| `height_range`           | Vertical excursion of ball within cycle                  |
| `switch_time_norm`       | Normalized time (0-1) when crossover occurs              |
