# Quickstart: Dribble Cycle Metrics Analysis

**Feature Branch**: `001-dribble-cycle-metrics`

## Prerequisites

- Python 3.13+
- Existing project dependencies installed (scipy, numpy, opencv-python, mediapipe)
- Reference video in `videos/reference.mov`

## Installation

No additional dependencies required. The feature uses existing project dependencies.

```bash
# Ensure you're on the feature branch
git checkout 001-dribble-cycle-metrics

# Install existing dependencies (if not already installed)
pip install scipy numpy opencv-python mediapipe
```

## New Configuration Options

Add these to your `Config` instance or modify `src/config.py`:

```python
# Control threshold: d_thr = k * shoulder_width_session
contact_threshold_k: float = 0.5

# Dominant hand margin (10% = 0.1)
dominant_hand_delta: float = 0.1

# Minimum frames for meaningful contact window
min_contact_window_frames: int = 3
```

## Basic Usage

### 1. Process Video and Get Metrics

```python
from config import Config
from main import VideoProcessor

# Initialize
config = Config()
processor = VideoProcessor(config)

# Process video (existing flow)
processor.process()
normalized_data = processor.normalizer.normalize(processor.frame_data_list)

# NEW: Get cycle metrics
from processors.contact_labeler import ContactLabeler
from processors.cycle_metrics import CycleMetrics
from processors.session_aggregator import SessionAggregator

# Step 1: Label contacts
labeler = ContactLabeler(
    k=config.contact_threshold_k,
    min_window_frames=config.min_contact_window_frames
)
labeled_frames, shoulder_width_session = labeler.label_frames(normalized_data)

# Step 2: Detect cycles and compute metrics
cycle_detector = CycleDetector(config.min_cycle_duration)
cycles_raw = cycle_detector.detect_cycles(normalized_data, fps=30)

metrics_computer = CycleMetrics(
    d_thr=config.contact_threshold_k * shoulder_width_session,
    delta=config.dominant_hand_delta,
    min_window_frames=config.min_contact_window_frames
)
cycles = [metrics_computer.compute_cycle_metrics(c, i) for i, c in enumerate(cycles_raw)]

# Step 3: Aggregate session statistics
aggregator = SessionAggregator()
summary = aggregator.compute_session_summary(
    cycles=cycles,
    total_frames=len(processor.frame_data_list),
    valid_frames=len([f for f in normalized_data if f is not None]),
    shoulder_width_session=shoulder_width_session,
    d_thr=config.contact_threshold_k * shoulder_width_session
)
```

### 2. Access Metrics

```python
# Per-cycle metrics
for cycle in summary.cycles:
    print(f"Cycle {cycle.cycle_id}:")
    print(f"  Duration: {cycle.duration_ms:.1f}ms")
    print(f"  Height range: {cycle.height_range:.3f}")
    print(f"  Controlled time: {cycle.controlled_time_ratio:.1%}")
    print(f"  Dominant hand: {cycle.dominant_hand or 'ambiguous'}")
    print(f"  Is crossover: {cycle.is_crossover}")
    print()

# Session summary
print("Session Summary:")
print(f"  Total cycles: {len(summary.cycles)}")
print(f"  Avg duration: {summary.duration_mean:.1f}ms (±{summary.duration_variance**0.5:.1f})")
print(f"  Crossovers: {summary.crossovers_count}")
print(f"  Left hand ratio: {summary.left_hand_ratio:.1%}")
print(f"  Right hand ratio: {summary.right_hand_ratio:.1%}")
print(f"  Control deviation: {summary.control_deviation_mean:.4f}")
```

## Output Data Structures

### Cycle Object

| Field                          | Type   | Description                               |
| ------------------------------ | ------ | ----------------------------------------- |
| `cycle_id`                     | int    | Unique identifier                         |
| `duration_ms`                  | float  | Cycle length in milliseconds              |
| `max_height`                   | float  | Highest ball position (min ball_y)        |
| `min_height`                   | float  | Lowest ball position (max ball_y, bounce) |
| `height_range`                 | float  | Vertical excursion                        |
| `contact_time_fraction_left`   | float  | % time with left hand contact             |
| `contact_time_fraction_right`  | float  | % time with right hand contact            |
| `controlled_time_ratio`        | float  | % time with any hand contact              |
| `start_hand`                   | str?   | First hand to contact ('L', 'R', None)    |
| `end_hand`                     | str?   | Last hand to contact ('L', 'R', None)     |
| `is_crossover`                 | bool?  | True if hand changed during cycle         |
| `dominant_hand`                | str?   | Hand with >10% more contact time          |
| `control_deviation_in_control` | float? | Avg ball-wrist distance during contact    |

### SessionSummary Object

| Field                    | Type  | Description                           |
| ------------------------ | ----- | ------------------------------------- |
| `cycles`                 | list  | All Cycle objects                     |
| `duration_mean`          | float | Average cycle duration                |
| `duration_variance`      | float | Variance of cycle durations           |
| `crossovers_count`       | int   | Number of crossover cycles            |
| `left_hand_ratio`        | float | % of non-crossover cycles using left  |
| `right_hand_ratio`       | float | % of non-crossover cycles using right |
| `control_deviation_mean` | float | Average control deviation             |

## Tuning Parameters

If metrics seem off, adjust these values:

| Parameter                   | Default | Adjust If...                          |
| --------------------------- | ------- | ------------------------------------- |
| `contact_threshold_k`       | 0.5     | Contact windows too short/long        |
| `dominant_hand_delta`       | 0.1     | Too many/few ambiguous dominant hands |
| `min_contact_window_frames` | 3       | Contact events seem noisy             |
| `min_cycle_duration`        | 10      | Cycles split incorrectly              |

## Testing

```bash
# Run all new tests
pytest tests/unit/test_contact_labeler.py
pytest tests/unit/test_cycle_metrics.py
pytest tests/unit/test_session_aggregator.py

# Run integration test
pytest tests/integration/test_metrics_pipeline.py

# Run with verbose output
pytest -v tests/
```

## Troubleshooting

### No cycles detected

- Check if video has enough valid frames (minimum 10)
- Verify ball is visible in frames
- Check normalization output for None frames

### All frames labeled 'unknown'

- Wrist detection may be failing
- Check pose detection confidence thresholds

### Unexpected crossover count

- Adjust `min_contact_window_frames` to filter noise
- Check if `contact_threshold_k` is appropriate for video scale

## Next Steps

After implementing this feature:

1. Run `/speckit.tasks` to generate implementation tasks
2. Implement processors in order: ContactLabeler → CycleMetrics → SessionAggregator
3. Write unit tests for each processor
4. Run integration test with reference video
