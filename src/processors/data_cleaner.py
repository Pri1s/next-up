"""Data cleaner module for outlier detection and interpolation."""

from typing import Optional


class DataCleaner:
    """
    Data cleaner for detecting and correcting outlier ball positions.
    
    This class handles velocity-based outlier detection and linear
    interpolation to fix impossible ball movements in tracking data.
    
    Attributes:
        max_velocity: Maximum pixels the ball can move per frame.
    """
    
    def __init__(self, max_velocity: int = 100):
        """
        Initializes the DataCleaner.
        
        Args:
            max_velocity: Maximum pixels the ball can move per frame (default: 100).
        """
        self.max_velocity = max_velocity
    
    def detect_outliers_by_velocity(
        self, 
        frame_data_list: list[dict]
    ) -> list[int]:
        """
        Identifies frames where ball movement is physically impossible.
        
        Detects outlier ball positions by calculating frame-to-frame movement.
        If the ball moves more than max_velocity pixels between frames, it's
        likely a tracking error.
        
        Args:
            frame_data_list: List of frame dictionaries with ball_center data.
        
        Returns:
            List of indices of frames with outlier ball positions.
        """
        outlier_indices = []
        
        for i in range(1, len(frame_data_list)):
            prev_pos = frame_data_list[i-1]['ball_center']
            curr_pos = frame_data_list[i]['ball_center']
            
            if prev_pos and curr_pos:
                dx = curr_pos[0] - prev_pos[0]
                dy = curr_pos[1] - prev_pos[1]
                distance = (dx**2 + dy**2)**0.5
                
                if distance > self.max_velocity:
                    outlier_indices.append(i)
        
        return outlier_indices
    
    def interpolate_outliers(
        self, 
        frame_data_list: list[dict], 
        outlier_indices: list[int]
    ) -> None:
        """
        Replaces outlier ball positions with linear interpolation.
        
        For each outlier frame, finds the nearest valid ball positions before
        and after, then linearly interpolates between them to estimate the
        correct ball position.
        
        Args:
            frame_data_list: List of frame dictionaries (modified in-place).
            outlier_indices: List of frame indices to interpolate.
        """
        for idx in outlier_indices:
            prev_idx = idx - 1
            next_idx = idx + 1
            
            while prev_idx >= 0 and (
                frame_data_list[prev_idx]['ball_center'] is None or 
                prev_idx in outlier_indices
            ):
                prev_idx -= 1
            
            while next_idx < len(frame_data_list) and (
                frame_data_list[next_idx]['ball_center'] is None or 
                next_idx in outlier_indices
            ):
                next_idx += 1
            
            if prev_idx >= 0 and next_idx < len(frame_data_list):
                prev_pos = frame_data_list[prev_idx]['ball_center']
                next_pos = frame_data_list[next_idx]['ball_center']
                
                if prev_pos and next_pos:
                    t = (idx - prev_idx) / (next_idx - prev_idx)
                    interp_x = int(prev_pos[0] + t * (next_pos[0] - prev_pos[0]))
                    interp_y = int(prev_pos[1] + t * (next_pos[1] - prev_pos[1]))
                    
                    frame_data_list[idx]['ball_center'] = (interp_x, interp_y)
    
    def clean(self, frame_data_list: list[dict]) -> list[dict]:
        """
        Cleans ball position data by detecting and correcting outliers.
        
        Uses velocity-based outlier detection to identify impossible ball
        movements, then applies linear interpolation to fix those positions.
        
        Args:
            frame_data_list: List of frame dictionaries with ball_center data.
        
        Returns:
            The cleaned frame_data_list (modified in-place, also returned).
        """
        print("Cleaning ball position data...")
        
        outliers = self.detect_outliers_by_velocity(frame_data_list)
        print(f"  Found {len(outliers)} outlier positions (moved >{self.max_velocity} pixels)")
        
        if outliers:
            self.interpolate_outliers(frame_data_list, outliers)
            print(f"  Corrected {len(outliers)} outlier positions using linear interpolation")
        
        return frame_data_list
