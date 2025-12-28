"""Video utility functions for video processing."""

import cv2
import numpy as np


def apply_orange_mask(frame: np.ndarray, lower_hsv: tuple[int, int, int], upper_hsv: tuple[int, int, int]) -> np.ndarray:
    """
    Applies color masking to isolate orange objects (basketball) in the frame.
    
    Args:
        frame: Video frame as numpy array (BGR format).
        lower_hsv: Lower HSV bound tuple for orange color.
        upper_hsv: Upper HSV bound tuple for orange color.
    
    Returns:
        Masked frame showing only orange-colored regions.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_orange = np.array(lower_hsv)
    upper_orange = np.array(upper_hsv)
    mask = cv2.inRange(hsv, lower_orange, upper_orange)
    masked_frame = cv2.bitwise_and(frame, frame, mask=mask)
    return masked_frame
