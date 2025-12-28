# next-up

Basketball video processing and dribble analysis system using MediaPipe and OpenCV.

## Architecture

The codebase follows a modular architecture with single responsibility principle:

```
src/
├── config.py              # Configuration management
├── detectors/             # Detection components
│   ├── ball_detector.py   # MediaPipe ball detection
│   └── pose_detector.py   # MediaPipe pose detection
├── trackers/              # Tracking components
│   └── ball_tracker.py    # OpenCV CSRT tracker
├── processors/            # Data processing components
│   ├── data_cleaner.py    # Outlier detection & interpolation
│   ├── normalizer.py      # Coordinate normalization
│   └── cycle_detector.py  # Dribble cycle detection
├── visualizers/           # Visualization components
│   └── frame_visualizer.py # Frame drawing utilities
├── utils/                 # Utility functions
│   └── video_utils.py     # Video processing helpers
└── main.py               # Main orchestrator
```

## Usage

### Running the refactored code:

```bash
source venv/bin/activate
python -m src.main
```

### Running the original code:

```bash
source venv/bin/activate
python main.py
```

## Module Overview

### Config (`src/config.py`)
- `Config`: Dataclass containing all paths and parameters

### Detectors (`src/detectors/`)
- `BallDetector`: Wraps MediaPipe ObjectDetector for basketball detection
- `PoseDetector`: Wraps MediaPipe PoseLandmarker for human pose detection

### Trackers (`src/trackers/`)
- `BallTracker`: Wraps OpenCV TrackerCSRT for ball tracking between detections

### Processors (`src/processors/`)
- `DataCleaner`: Velocity-based outlier detection and linear interpolation
- `CoordinateNormalizer`: Body-relative coordinate transformation
- `CycleDetector`: Peak-based dribble cycle segmentation

### Visualizers (`src/visualizers/`)
- `FrameVisualizer`: All drawing functions for video visualization

### Utils (`src/utils/`)
- `apply_orange_mask`: Orange color masking for basketball isolation

### Main (`src/main.py`)
- `VideoProcessor`: Orchestrates all components for video processing
- `main()`: Entry point function
