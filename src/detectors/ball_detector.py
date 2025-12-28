"""Ball detector module using MediaPipe ObjectDetector."""

import mediapipe as mp
from mediapipe.tasks.python import vision
import numpy as np
from typing import Optional


class BallDetector:
    """
    Ball detector using MediaPipe ObjectDetector for basketball detection.
    
    This class wraps the MediaPipe ObjectDetector to detect basketballs
    (sports balls) in video frames.
    
    Attributes:
        detector: MediaPipe ObjectDetector instance.
        config: Configuration object with detection parameters.
    """
    
    def __init__(self, config):
        """
        Initializes the BallDetector.
        
        Args:
            config: Config object containing model path and detection parameters.
        """
        self.config = config
        self.detector = self._create_detector()
    
    def _create_detector(self) -> vision.ObjectDetector:
        """
        Creates and configures a MediaPipe ObjectDetector.
        
        Returns:
            ObjectDetector: Configured detector instance for video processing.
        """
        base_options = mp.tasks.BaseOptions(
            model_asset_path=self.config.object_detection_model_path
        )
        options = vision.ObjectDetectorOptions(
            base_options=base_options,
            max_results=self.config.detection_max_results,
            score_threshold=self.config.detection_score_threshold,
            category_allowlist=['sports ball'],
            running_mode=vision.RunningMode.VIDEO
        )
        return vision.ObjectDetector.create_from_options(options)
    
    def detect(self, frame: np.ndarray, timestamp_ms: int) -> Optional[tuple[int, int, int, int]]:
        """
        Detects basketball in a video frame.
        
        Args:
            frame: Video frame as numpy array (BGR format).
            timestamp_ms: Frame timestamp in milliseconds.
        
        Returns:
            Tuple of (x, y, w, h) bounding box coordinates, or None if no ball detected.
        """
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        if result.detections:
            detection = result.detections[0]
            bounding_box = detection.bounding_box
            
            x = int(bounding_box.origin_x)
            y = int(bounding_box.origin_y)
            w = int(bounding_box.width)
            h = int(bounding_box.height)
            
            return (x, y, w, h)
        return None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.detector.close()
