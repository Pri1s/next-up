# Implementation Plan: Dribble Cycle Metrics Analysis

**Branch**: `001-dribble-cycle-metrics` | **Date**: 2024-12-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-dribble-cycle-metrics/spec.md`

## Summary

Extend the existing dribble cycle detection pipeline to compute comprehensive per-cycle metrics (timing, ball height, hand contact, control deviation) and session-level aggregates. The feature builds on the existing `CoordinateNormalizer` and `CycleDetector` classes, adding contact labeling, cycle metrics computation, and session aggregation while respecting the constitution's frames → cycles → aggregates pipeline.

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: scipy (signal processing), numpy (numerical operations), opencv-python (cv2), mediapipe (pose detection)  
**Storage**: In-memory data structures; no persistent storage required  
**Testing**: pytest with unit tests for each processor component  
**Target Platform**: macOS/Linux (local development)  
**Project Type**: Single Python project with modular processors  
**Performance Goals**: Process 60-second video (~1800 frames at 30fps) in under 10 seconds  
**Constraints**: All metrics must be deterministic and reproducible; no AI in evaluation layer  
**Scale/Scope**: Single-user local processing; one video at a time

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

| Principle                                   | Status  | Evidence                                                                         |
| ------------------------------------------- | ------- | -------------------------------------------------------------------------------- |
| **1. Separation of Responsibilities**       | ✅ PASS | Feature is entirely in Evaluation layer; no Perception or Interpretation changes |
| **2. Frame-Level Data Is Source of Truth**  | ✅ PASS | All metrics derived from NormalizedFrame data; frame_index preserved             |
| **3. Temporal Information Preserved**       | ✅ PASS | Pipeline: Frames → Cycles → Cycle Metrics → Session Aggregates                   |
| **4. Normalization Is Mandatory**           | ✅ PASS | Uses existing CoordinateNormalizer; all distances in body-height units           |
| **5. Cycles Represent Atomic Motion Units** | ✅ PASS | Extends existing CycleDetector; one cycle = one dribble                          |
| **6. Metrics Must Be Explainable**          | ✅ PASS | Each metric has physical meaning documented in spec                              |
| **7. Aggregates Are Summaries**             | ✅ PASS | Session stats computed from cycle table; cycle data preserved                    |
| **8. AI Is Interpreter Only**               | ✅ PASS | No AI components in this feature                                                 |
| **9. Controlled Recording Assumptions**     | ✅ PASS | Stationary dribbling mode; documented in spec                                    |
| **10. Scalability**                         | ✅ PASS | New metrics added without breaking existing pipeline                             |

**Gate Result**: ✅ ALL GATES PASS — Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/001-dribble-cycle-metrics/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── config.py                    # Configuration (add new constants: k, delta)
├── main.py                      # VideoProcessor orchestrator
├── detectors/
│   ├── ball_detector.py         # [existing] Ball detection
│   └── pose_detector.py         # [existing] Pose detection
├── trackers/
│   └── ball_tracker.py          # [existing] Ball tracking
├── processors/
│   ├── normalizer.py            # [existing] Coordinate normalization
│   ├── cycle_detector.py        # [existing] Cycle boundary detection
│   ├── contact_labeler.py       # [NEW] Per-frame contact labeling (FR-009 to FR-015)
│   ├── cycle_metrics.py         # [NEW] Per-cycle metric computation (FR-019 to FR-024)
│   └── session_aggregator.py    # [NEW] Session-level statistics (FR-025 to FR-027)
├── models/
│   ├── labeled_frame.py         # [NEW] LabeledFrame dataclass
│   ├── contact_event.py         # [NEW] ContactEvent dataclass
│   ├── cycle.py                 # [NEW] Cycle dataclass with metrics
│   └── session_summary.py       # [NEW] SessionSummary dataclass
├── utils/
│   └── video_utils.py           # [existing] Video utilities
└── visualizers/
    └── frame_visualizer.py      # [existing] Visualization

tests/
├── unit/
│   ├── test_contact_labeler.py  # [NEW] Contact labeling tests
│   ├── test_cycle_metrics.py    # [NEW] Cycle metrics tests
│   └── test_session_aggregator.py # [NEW] Session aggregation tests
└── integration/
    └── test_metrics_pipeline.py # [NEW] End-to-end pipeline test
```

**Structure Decision**: Single Python project (Option 1). All new code fits within existing `src/processors/` and new `src/models/` directories. Tests follow pytest conventions in `tests/` directory.

## Complexity Tracking

> No constitution violations — table not required.
