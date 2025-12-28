"""Coordinate normalizer module for body-relative coordinate transformation."""

from typing import Optional


class CoordinateNormalizer:
    """
    Coordinate normalizer for body-relative position transformation.
    
    This class normalizes absolute pixel coordinates to body-relative
    proportions, making the data invariant to player size, camera distance,
    and frame resolution.
    """
    
    def __init__(self):
        """Initializes the CoordinateNormalizer."""
        pass
    
    def _normalize_position(
        self, 
        pos: Optional[tuple[int, int]], 
        hip_center: tuple[int, int], 
        body_height: float
    ) -> Optional[tuple[float, float]]:
        """
        Normalizes a single position coordinate.
        
        Args:
            pos: Position tuple (x, y) or None.
            hip_center: Hip center coordinates (x, y).
            body_height: Body height in pixels.
        
        Returns:
            Normalized position tuple (x, y) or None.
        """
        if pos is None:
            return None
        
        rel_x = pos[0] - hip_center[0]
        rel_y = pos[1] - hip_center[1]
        norm_x = rel_x / body_height
        norm_y = rel_y / body_height
        
        return (norm_x, norm_y)
    
    def normalize(self, frame_data_list: list[dict]) -> list[Optional[dict]]:
        """
        Normalizes all position coordinates relative to hip center and body height.
        
        Converts absolute pixel coordinates to body-relative proportions, making
        the data invariant to player size, camera distance, and frame resolution.
        
        Normalization process:
        - Origin: Hip center becomes (0, 0)
        - Scale: Divide by body height (shoulder center to hip center distance)
        - Result: All positions expressed as proportions of body size
        
        Args:
            frame_data_list: List of frame dictionaries with absolute pixel coordinates.
        
        Returns:
            New list with normalized coordinates, or None for frames without pose data.
        """
        normalized_data_list = []
        
        print("Normalizing coordinates...")
        frames_normalized = 0
        frames_skipped = 0
        
        for frame_data in frame_data_list:
            hip_center = frame_data.get('hip_center')
            left_shoulder = frame_data.get('left_shoulder')
            right_shoulder = frame_data.get('right_shoulder')
            
            if not hip_center or not left_shoulder or not right_shoulder:
                normalized_data_list.append(None)
                frames_skipped += 1
                continue
            
            shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
            shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
            
            dx = shoulder_center_x - hip_center[0]
            dy = shoulder_center_y - hip_center[1]
            body_height = (dx**2 + dy**2)**0.5
            
            if body_height < 10:
                normalized_data_list.append(None)
                frames_skipped += 1
                continue
            
            normalized_frame = {
                'frame_index': frame_data['frame_index'],
                'timestamp_ms': frame_data['timestamp_ms'],
                'ball_center': self._normalize_position(
                    frame_data.get('ball_center'), hip_center, body_height
                ),
                'left_wrist': self._normalize_position(
                    frame_data.get('left_wrist'), hip_center, body_height
                ),
                'right_wrist': self._normalize_position(
                    frame_data.get('right_wrist'), hip_center, body_height
                ),
                'left_elbow': self._normalize_position(
                    frame_data.get('left_elbow'), hip_center, body_height
                ),
                'right_elbow': self._normalize_position(
                    frame_data.get('right_elbow'), hip_center, body_height
                ),
                'left_shoulder': self._normalize_position(
                    frame_data.get('left_shoulder'), hip_center, body_height
                ),
                'right_shoulder': self._normalize_position(
                    frame_data.get('right_shoulder'), hip_center, body_height
                ),
                'left_knee': self._normalize_position(
                    frame_data.get('left_knee'), hip_center, body_height
                ),
                'right_knee': self._normalize_position(
                    frame_data.get('right_knee'), hip_center, body_height
                ),
                'hip_center': (0.0, 0.0),
                'body_height': 1.0
            }
            
            normalized_data_list.append(normalized_frame)
            frames_normalized += 1
        
        print(f"  Normalized {frames_normalized} frames")
        print(f"  Skipped {frames_skipped} frames (missing pose data)")
        
        return normalized_data_list
