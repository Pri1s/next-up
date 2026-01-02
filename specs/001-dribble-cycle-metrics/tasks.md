# Tasks: Dribble Cycle Metrics Analysis

**Input**: Design documents from `/specs/001-dribble-cycle-metrics/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Not included (tests were not explicitly requested in feature specification).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `models/` at repository root
- Paths follow existing project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new configuration constants and create models directory structure

- [ ] T001 Add configuration constants (k=0.5, delta=0.1, min_contact_window_frames=3) to `src/config.py`
- [ ] T002 [P] Create `src/models/__init__.py` module initialization file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until these models exist

- [ ] T003 [P] Create LabeledFrame dataclass in `src/models/labeled_frame.py` per data-model.md specification
- [ ] T004 [P] Create ContactEvent dataclass in `src/models/contact_event.py` per data-model.md specification
- [ ] T005 [P] Create Cycle dataclass in `src/models/cycle.py` per data-model.md specification
- [ ] T006 [P] Create SessionSummary dataclass in `src/models/session_summary.py` per data-model.md specification
- [ ] T007 Update `src/models/__init__.py` to export all dataclasses

**Checkpoint**: All data models ready - processor implementation can begin

---

## Phase 3: User Story 1 - Analyze Complete Dribbling Session (Priority: P1) 🎯 MVP

**Goal**: Transform video into cycle boundaries, per-cycle metrics, and session aggregates

**Independent Test**: Process reference.mov and verify output contains valid cycle boundaries, timing/height metrics per cycle, and session averages (mean/variance)

### Implementation for User Story 1

- [ ] T008 [US1] Create ContactLabeler class in `src/processors/contact_labeler.py` implementing:
  - Shoulder width computation (FR-009, FR-010)
  - Session-level d_thr calculation (FR-011)
  - Per-frame distance computation (FR-012, FR-013, FR-015)
  - Frame labeling logic (FR-014)
- [ ] T009 [US1] Create CycleMetrics class in `src/processors/cycle_metrics.py` implementing:
  - Timing metrics: start_time, end_time, duration (FR-019)
  - Ball height metrics: max_height, min_height, avg_height, height_range (FR-020)
  - Contact windows grouping (FR-016, FR-017, FR-018)
- [ ] T010 [US1] Create SessionAggregator class in `src/processors/session_aggregator.py` implementing:
  - Mean and variance for duration, max_height, controlled_time_ratio (FR-025 partial)
- [ ] T011 [US1] Update `src/processors/__init__.py` to export new processors
- [ ] T012 [US1] Integrate ContactLabeler into VideoProcessor in `src/main.py`
- [ ] T013 [US1] Integrate CycleMetrics into VideoProcessor in `src/main.py`
- [ ] T014 [US1] Integrate SessionAggregator into VideoProcessor in `src/main.py`
- [ ] T015 [US1] Add print/logging output of session summary metrics in `src/main.py`

**Checkpoint**: User Story 1 complete - system produces cycle boundaries and basic metrics for any video

---

## Phase 4: User Story 2 - Identify Hand Usage Patterns (Priority: P2)

**Goal**: Label per-frame hand contact, detect crossovers, compute hand ratios

**Independent Test**: Process a video with known crossover dribbles and verify crossover cycles are correctly identified with start_hand/end_hand and session hand ratios sum to ~1.0

### Implementation for User Story 2

- [ ] T016 [US2] Extend CycleMetrics in `src/processors/cycle_metrics.py` to compute contact timing metrics:
  - contact_time_fraction_left (FR-021)
  - contact_time_fraction_right (FR-021)
  - controlled_time_ratio (FR-021)
- [ ] T017 [US2] Extend CycleMetrics in `src/processors/cycle_metrics.py` to determine hand fields:
  - start_hand from first meaningful contact window (FR-022)
  - end_hand from last meaningful contact window (FR-022)
  - is_crossover detection (FR-022)
  - dominant_hand with delta margin (FR-022)
- [ ] T018 [US2] Add switch_time_norm computation for crossover cycles in `src/processors/cycle_metrics.py` (FR-023)
- [ ] T019 [US2] Extend SessionAggregator in `src/processors/session_aggregator.py` to compute:
  - crossovers_count (FR-026)
  - left_hand_ratio and right_hand_ratio (FR-027)
- [ ] T020 [US2] Update session summary output in `src/main.py` to include hand metrics

**Checkpoint**: User Story 2 complete - system identifies hand usage patterns and crossovers

---

## Phase 5: User Story 3 - Measure Ball Control Quality (Priority: P3)

**Goal**: Compute control deviation metrics indicating ball-wrist proximity

**Independent Test**: Compare control_deviation_in_control between two videos - skilled player should show lower values

### Implementation for User Story 3

- [ ] T021 [US3] Extend CycleMetrics in `src/processors/cycle_metrics.py` to compute:
  - control_deviation_overall: mean d_min over all frames with wrists (FR-024)
  - control_deviation_in_control: mean d_min over frames labeled L or R (FR-024)
- [ ] T022 [US3] Extend SessionAggregator in `src/processors/session_aggregator.py` to compute:
  - control_deviation_mean across all cycles (FR-025)
  - control_deviation_variance across all cycles (FR-025)
- [ ] T023 [US3] Update session summary output in `src/main.py` to include control deviation metrics

**Checkpoint**: All user stories complete - full metrics pipeline functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation, documentation, and cleanup

- [ ] T024 [P] Verify all metrics are deterministic by running pipeline twice on reference.mov and comparing outputs
- [ ] T025 [P] Add docstrings to all new classes and methods following existing code style
- [ ] T026 Run full pipeline on reference.mov and document sample output in quickstart.md
- [ ] T027 Update README.md with new metrics capabilities

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup
    │
    ▼
Phase 2: Foundational (Data Models)
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
Phase 3: US1       Phase 4: US2       Phase 5: US3
(can start         (depends on        (depends on
immediately)       US1 T008-T009)     US2 T016-T017)
    │                  │                  │
    └──────────────────┴──────────────────┘
                       │
                       ▼
               Phase 6: Polish
```

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on ContactLabeler (T008) and CycleMetrics base (T009) from US1
- **User Story 3 (P3)**: Depends on contact labeling from US2 (T016-T017) for d_min filtering

### Within Each User Story

- Models before processors
- Processors before main.py integration
- Core computation before output/logging

### Parallel Opportunities

- T003, T004, T005, T006 (all data models) can run in parallel
- T024, T025 (polish tasks) can run in parallel
- Different user stories can be worked on sequentially (dependencies exist)

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all model creation tasks together:
Task: "Create LabeledFrame dataclass in src/models/labeled_frame.py"
Task: "Create ContactEvent dataclass in src/models/contact_event.py"
Task: "Create Cycle dataclass in src/models/cycle.py"
Task: "Create SessionSummary dataclass in src/models/session_summary.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T007)
3. Complete Phase 3: User Story 1 (T008-T015)
4. **STOP and VALIDATE**: Run on reference.mov, verify cycle detection and basic metrics
5. Demo/validate before proceeding

### Incremental Delivery

1. Setup + Foundational → Models ready
2. Add User Story 1 → Cycle detection + timing/height metrics (MVP!)
3. Add User Story 2 → Hand labeling + crossover detection
4. Add User Story 3 → Control deviation metrics
5. Each story adds metrics without breaking previous functionality

---

## Task Summary

| Phase        | Tasks     | Purpose                     |
| ------------ | --------- | --------------------------- |
| Setup        | T001-T002 | Configuration and structure |
| Foundational | T003-T007 | Data models (blocking)      |
| User Story 1 | T008-T015 | Core metrics pipeline (MVP) |
| User Story 2 | T016-T020 | Hand usage patterns         |
| User Story 3 | T021-T023 | Control deviation           |
| Polish       | T024-T027 | Validation and docs         |

**Total Tasks**: 27
**MVP Tasks** (US1 only): 15 (T001-T015)
**Parallel Opportunities**: 8 tasks marked [P]

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story builds on previous but adds independent value
- Commit after each task or logical group
- Validate with reference.mov after each user story checkpoint
- All metrics must be deterministic (same input → same output)
