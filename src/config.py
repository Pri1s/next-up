"""Configuration module for video processing parameters and paths."""

from dataclasses import dataclass


@dataclass
class Config:
    """
    Configuration class containing all paths and parameters for video processing.
    
    Attributes:
        object_detection_model_path: Path to the object detection model file.
        pose_model_path: Path to the pose landmarker model file.
        reference_video_path: Path to the reference video file.
        detect_every_n_frames: Number of frames between object detections.
        max_velocity: Maximum pixels the ball can move per frame.
        min_cycle_duration: Minimum frames between dribble cycle troughs.
        contact_threshold_k: Control threshold multiplier for hand contact.
        dominant_hand_delta: Margin threshold for dominant hand detection.
        min_contact_window_frames: Minimum frames for meaningful contact.
        detection_score_threshold: Minimum confidence score for object detection.
        detection_max_results: Maximum number of detection results.
        min_ball_area_ratio: Minimum ball bbox area ratio relative to frame.
        max_ball_area_ratio: Maximum ball bbox area ratio relative to frame.
        min_orange_ratio: Minimum orange pixel ratio inside bbox.
        min_detect_track_iou: Minimum IoU to consider detect/track agreement.
        max_track_acceleration: Maximum pixel acceleration between frames.
        force_detect_frames: Frames to force detection after a rejection.
        tracking_grace_frames: Frames to hold last good ball center after rejection.
        crossover_hand_gap_tolerance: Cycles to skip when counting hand transitions.
        pose_detection_confidence: Minimum confidence for pose detection.
        pose_presence_confidence: Minimum confidence for pose presence.
        pose_tracking_confidence: Minimum confidence for pose tracking.
        num_poses: Maximum number of poses to detect.
        orange_mask_lower: Lower HSV bound for orange color mask.
        orange_mask_upper: Upper HSV bound for orange color mask.
    """
    
    # Model paths
    object_detection_model_path: str = "models/efficientdet_lite0.tflite"
    pose_model_path: str = "models/pose_landmarker_full.task"
    
    # Video paths
    reference_video_path: str = "videos/reference.mov"
    
    # Detection parameters
    detect_every_n_frames: int = 10
    max_velocity: int = 100
    # Minimum frames between troughs - lowered to allow fast bounces as separate cycles
    # Only filters obvious jitter troughs; real quick dribbles survive
    min_cycle_duration: int = 3

    # Control threshold: d_thr = k * shoulder_width_session
    # Increased from 0.75 to 1.0 so L/R labels appear more often
    contact_threshold_k: float = 1.0

    # Dominant hand margin
    dominant_hand_delta: float = 0.1

    # Minimum frames for meaningful contact window
    # Lowered to 2 so short but real hand contacts per bounce aren't discarded
    min_contact_window_frames: int = 2
    
    # Object detection parameters
    detection_score_threshold: float = 0.3
    detection_max_results: int = 1

    # Tracking validation parameters
    min_ball_area_ratio: float = 0.0003
    max_ball_area_ratio: float = 0.08
    min_orange_ratio: float = 0.08
    min_detect_track_iou: float = 0.1
    max_track_acceleration: float = 300.0
    force_detect_frames: int = 5
    tracking_grace_frames: int = 3
    crossover_hand_gap_tolerance: int = 1
    
    # Pose detection parameters
    pose_detection_confidence: float = 0.5
    pose_presence_confidence: float = 0.5
    pose_tracking_confidence: float = 0.5
    num_poses: int = 1
    
    # Orange mask HSV bounds
    orange_mask_lower: tuple[int, int, int] = (5, 100, 100)
    orange_mask_upper: tuple[int, int, int] = (20, 255, 255)
