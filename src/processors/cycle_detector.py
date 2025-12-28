"""Cycle detector module for dribble cycle detection."""

from scipy.signal import find_peaks
from typing import Optional


class CycleDetector:
    """
    Cycle detector for identifying individual dribble cycles.
    
    This class uses peak detection on ball height data to segment
    the video into individual dribble cycles.
    
    Attributes:
        min_cycle_duration: Minimum frames between peaks.
    """
    
    def __init__(self, min_cycle_duration: int = 10):
        """
        Initializes the CycleDetector.
        
        Args:
            min_cycle_duration: Minimum frames between peaks to avoid splitting
                               one dribble into multiple cycles (default: 10).
        """
        self.min_cycle_duration = min_cycle_duration
    
    def detect_cycles(
        self, 
        normalized_data_list: list[Optional[dict]], 
        fps: float
    ) -> list[list[dict]]:
        """
        Detects individual dribble cycles by finding peaks in ball height.
        
        Uses SciPy's find_peaks to identify local maxima (peaks) in the ball's
        vertical position. The frames between consecutive peaks represent one
        complete dribble cycle (ball going down and coming back up).
        
        Args:
            normalized_data_list: List of normalized frame dictionaries.
            fps: Frames per second of the video.
        
        Returns:
            List of dribble cycles, where each cycle is a list of frame data.
        """
        print("Detecting dribble cycles...")
        
        ball_heights = []
        valid_frame_indices = []
        
        for frame in normalized_data_list:
            if frame and frame.get('ball_center'):
                ball_heights.append(-frame['ball_center'][1])
                valid_frame_indices.append(frame['frame_index'])
            else:
                ball_heights.append(None)
                valid_frame_indices.append(None)
        
        valid_heights = [h for h in ball_heights if h is not None]
        valid_indices = [i for i, h in enumerate(ball_heights) if h is not None]
        
        if len(valid_heights) < self.min_cycle_duration:
            print(f"  Not enough valid data points ({len(valid_heights)}) for cycle detection")
            return []
        
        peaks, properties = find_peaks(
            valid_heights,
            distance=self.min_cycle_duration,
            prominence=0.1
        )
        
        peak_frame_indices = [valid_indices[p] for p in peaks]
        
        print(f"  Found {len(peak_frame_indices)} peaks (dribble cycle markers)")
        print(f"  Peak frames: {peak_frame_indices}")
        
        dribble_cycles = []
        
        for i in range(len(peak_frame_indices) - 1):
            start_idx = peak_frame_indices[i]
            end_idx = peak_frame_indices[i + 1]
            
            cycle_frames = []
            for frame in normalized_data_list:
                if frame and start_idx <= frame['frame_index'] < end_idx:
                    cycle_frames.append(frame)
            
            if len(cycle_frames) >= self.min_cycle_duration:
                dribble_cycles.append(cycle_frames)
                duration_ms = cycle_frames[-1]['timestamp_ms'] - cycle_frames[0]['timestamp_ms']
                print(f"  Cycle {len(dribble_cycles)}: {len(cycle_frames)} frames ({duration_ms}ms)")
        
        print(f"  Total dribble cycles detected: {len(dribble_cycles)}")
        
        return dribble_cycles
