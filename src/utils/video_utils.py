"""Video utility functions for video processing."""

import cv2
import numpy as np


def apply_orange_mask(
    frame: np.ndarray,
    lower_hsv: tuple[int, int, int],
    upper_hsv: tuple[int, int, int]
) -> np.ndarray:
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


def clamp_bbox(
    bbox: tuple[int, int, int, int],
    frame_shape: tuple[int, int, int]
) -> tuple[int, int, int, int]:
    """Clamps a bbox to image boundaries."""
    x, y, w, h = bbox
    height, width = frame_shape[:2]
    x = max(0, min(x, width - 1))
    y = max(0, min(y, height - 1))
    w = max(0, min(w, width - x))
    h = max(0, min(h, height - y))
    return x, y, w, h


def bbox_area_ratio(
    bbox: tuple[int, int, int, int],
    frame_shape: tuple[int, int, int]
) -> float:
    """Returns bbox area ratio relative to the full frame."""
    _, _, w, h = bbox
    height, width = frame_shape[:2]
    frame_area = max(1, height * width)
    return (w * h) / frame_area


def bbox_orange_ratio(
    masked_frame: np.ndarray,
    bbox: tuple[int, int, int, int]
) -> float:
    """Returns ratio of non-zero (orange) pixels inside bbox."""
    x, y, w, h = clamp_bbox(bbox, masked_frame.shape)
    if w == 0 or h == 0:
        return 0.0
    roi = masked_frame[y:y + h, x:x + w]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    orange_pixels = cv2.countNonZero(gray)
    return orange_pixels / (w * h)


def bbox_iou(
    bbox_a: tuple[int, int, int, int],
    bbox_b: tuple[int, int, int, int]
) -> float:
    """Computes IoU between two bboxes."""
    ax, ay, aw, ah = bbox_a
    bx, by, bw, bh = bbox_b
    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh

    inter_x1 = max(ax, bx)
    inter_y1 = max(ay, by)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    union_area = (aw * ah) + (bw * bh) - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area
