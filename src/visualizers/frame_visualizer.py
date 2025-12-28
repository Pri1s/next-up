"""Frame visualizer module for drawing on video frames."""

import cv2
import numpy as np
from typing import Optional


class FrameVisualizer:
    """
    Frame visualizer for drawing tracking information on video frames.
    
    This class contains all drawing functions to visualize ball detection,
    tracking, pose landmarks, and debug information on video frames.
    """
    
    def __init__(self):
        """Initializes the FrameVisualizer."""
        pass
    
    def draw_bounding_box(
        self, 
        frame: np.ndarray, 
        bbox: tuple[int, int, int, int], 
        color: tuple[int, int, int], 
        label: str
    ) -> None:
        """
        Draws a bounding box with label on a video frame.
        
        Args:
            frame: Video frame to draw on (modified in-place).
            bbox: Tuple of (x, y, w, h) bounding box coordinates.
            color: BGR color tuple for the box and text.
            label: String label to display above the box.
        """
        x, y, w, h = bbox
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, label, (x, y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    def draw_ball_center(
        self, 
        frame: np.ndarray, 
        center: tuple[int, int]
    ) -> None:
        """
        Draws a red dot at the ball's center position.
        
        Args:
            frame: Video frame to draw on (modified in-place).
            center: Tuple of (x, y) center coordinates.
        """
        cv2.circle(frame, center, 5, (0, 0, 255), -1)
    
    def draw_info(
        self, 
        frame: np.ndarray, 
        frame_index: int, 
        method: str, 
        frames_since_detection: int
    ) -> None:
        """
        Draws debug information on the video frame.
        
        Args:
            frame: Video frame to draw on (modified in-place).
            frame_index: Current frame number.
            method: String describing detection/tracking method used.
            frames_since_detection: Number of frames since last detection.
        """
        cv2.putText(frame, f"Frame: {frame_index}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Method: {method}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Frames since detect: {frames_since_detection}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def draw_ball_lost(self, frame: np.ndarray) -> None:
        """
        Draws "BALL LOST" message on the video frame.
        
        Args:
            frame: Video frame to draw on (modified in-place).
        """
        cv2.putText(frame, "BALL LOST", (50, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    
    def draw_pose_landmarks(
        self, 
        frame: np.ndarray, 
        pose_data: Optional[dict[str, tuple[int, int]]]
    ) -> None:
        """
        Draws circles and labels for detected pose landmarks.
        
        Args:
            frame: Video frame to draw on (modified in-place).
            pose_data: Dictionary of landmark positions or None.
        """
        if not pose_data:
            return
        
        for name, pos in pose_data.items():
            cv2.circle(frame, pos, 5, (0, 255, 0), -1)
            cv2.putText(frame, name, (pos[0] + 10, pos[1]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
