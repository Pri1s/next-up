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
        min_cycle_duration: Minimum frames between dribble cycle peaks.
        detection_score_threshold: Minimum confidence score for object detection.
        detection_max_results: Maximum number of detection results.
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
    min_cycle_duration: int = 10
    
    # Object detection parameters
    detection_score_threshold: float = 0.3
    detection_max_results: int = 1
    
    # Pose detection parameters
    pose_detection_confidence: float = 0.5
    pose_presence_confidence: float = 0.5
    pose_tracking_confidence: float = 0.5
    num_poses: int = 1
    
    # Orange mask HSV bounds
    orange_mask_lower: tuple[int, int, int] = (5, 100, 100)
    orange_mask_upper: tuple[int, int, int] = (20, 255, 255)
