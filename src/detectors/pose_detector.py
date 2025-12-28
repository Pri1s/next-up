"""Pose detector module using MediaPipe PoseLandmarker."""

import mediapipe as mp
from mediapipe.tasks.python import vision
import cv2
import numpy as np
from typing import Optional


class PoseDetector:
    """
    Pose detector using MediaPipe PoseLandmarker for human pose detection.
    
    This class wraps the MediaPipe PoseLandmarker to detect human body
    landmarks in video frames.
    
    Attributes:
        landmarker: MediaPipe PoseLandmarker instance.
        config: Configuration object with pose detection parameters.
    """
    
    def __init__(self, config):
        """
        Initializes the PoseDetector.
        
        Args:
            config: Config object containing model path and pose detection parameters.
        """
        self.config = config
        self.landmarker = self._create_landmarker()
    
    def _create_landmarker(self) -> vision.PoseLandmarker:
        """
        Creates and configures a MediaPipe PoseLandmarker.
        
        Returns:
            PoseLandmarker: Configured pose landmarker instance.
        """
        base_options = mp.tasks.BaseOptions(
            model_asset_path=self.config.pose_model_path
        )
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=self.config.num_poses,
            min_pose_detection_confidence=self.config.pose_detection_confidence,
            min_pose_presence_confidence=self.config.pose_presence_confidence,
            min_tracking_confidence=self.config.pose_tracking_confidence
        )
        return vision.PoseLandmarker.create_from_options(options)
    
    def detect(self, frame: np.ndarray, timestamp_ms: int) -> Optional[dict[str, tuple[int, int]]]:
        """
        Detects human pose landmarks in a frame.
        
        Args:
            frame: Video frame as numpy array (BGR format).
            timestamp_ms: Timestamp of the frame in milliseconds.
        
        Returns:
            Dictionary containing landmark positions or None if no pose detected.
            Keys: 'left_wrist', 'right_wrist', 'left_elbow', 'right_elbow',
                  'left_shoulder', 'right_shoulder', 'left_hip', 'right_hip',
                  'left_knee', 'right_knee', 'hip_center'
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        results = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        
        if not results.pose_landmarks or len(results.pose_landmarks) == 0:
            return None
        
        landmarks = results.pose_landmarks[0]
        h, w = frame.shape[:2]
        
        # MediaPipe Pose landmark indices
        left_wrist = landmarks[15]
        right_wrist = landmarks[16]
        left_elbow = landmarks[13]
        right_elbow = landmarks[14]
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        left_knee = landmarks[25]
        right_knee = landmarks[26]
        
        hip_center_x = (left_hip.x + right_hip.x) / 2
        hip_center_y = (left_hip.y + right_hip.y) / 2
        
        return {
            'left_wrist': (int(left_wrist.x * w), int(left_wrist.y * h)),
            'right_wrist': (int(right_wrist.x * w), int(right_wrist.y * h)),
            'left_elbow': (int(left_elbow.x * w), int(left_elbow.y * h)),
            'right_elbow': (int(right_elbow.x * w), int(right_elbow.y * h)),
            'left_shoulder': (int(left_shoulder.x * w), int(left_shoulder.y * h)),
            'right_shoulder': (int(right_shoulder.x * w), int(right_shoulder.y * h)),
            'left_hip': (int(left_hip.x * w), int(left_hip.y * h)),
            'right_hip': (int(right_hip.x * w), int(right_hip.y * h)),
            'left_knee': (int(left_knee.x * w), int(left_knee.y * h)),
            'right_knee': (int(right_knee.x * w), int(right_knee.y * h)),
            'hip_center': (int(hip_center_x * w), int(hip_center_y * h))
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.landmarker.close()
