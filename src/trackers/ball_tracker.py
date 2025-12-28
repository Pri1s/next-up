"""Ball tracker module using OpenCV TrackerCSRT."""

import cv2
import numpy as np
from typing import Optional


class BallTracker:
    """
    Ball tracker using OpenCV TrackerCSRT for basketball tracking.
    
    This class wraps the OpenCV TrackerCSRT to track a basketball
    across video frames after initial detection.
    
    Attributes:
        tracker: OpenCV TrackerCSRT instance, or None if not initialized.
        tracking_active: Boolean indicating if tracking is currently active.
    """
    
    def __init__(self):
        """Initializes the BallTracker."""
        self.tracker: Optional[cv2.legacy.Tracker] = None
        self.tracking_active: bool = False
    
    def initialize(self, frame: np.ndarray, bbox: tuple[int, int, int, int]) -> None:
        """
        Initializes the tracker with a frame and bounding box.
        
        Args:
            frame: Video frame as numpy array (BGR format).
            bbox: Tuple of (x, y, w, h) bounding box coordinates.
        """
        self.tracker = cv2.legacy.TrackerCSRT_create()
        self.tracker.init(frame, bbox)
        self.tracking_active = True
    
    def update(self, frame: np.ndarray) -> Optional[tuple[int, int, int, int]]:
        """
        Updates the tracker with a new frame.
        
        Args:
            frame: Video frame as numpy array (BGR format).
        
        Returns:
            Tuple of (x, y, w, h) bounding box coordinates, or None if tracking failed.
        """
        if not self.tracking_active or self.tracker is None:
            return None
        
        success, bbox = self.tracker.update(frame)
        if success:
            x, y, w, h = [int(v) for v in bbox]
            return (x, y, w, h)
        
        self.tracking_active = False
        return None
    
    def reset(self) -> None:
        """Resets the tracker state."""
        self.tracker = None
        self.tracking_active = False
    
    def is_active(self) -> bool:
        """
        Checks if tracking is currently active.
        
        Returns:
            Boolean indicating tracking status.
        """
        return self.tracking_active
