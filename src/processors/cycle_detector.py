"""Cycle detector module for dribble cycle detection."""

from scipy.signal import find_peaks


class CycleDetector:
    """
    Cycle detector for identifying individual dribble cycles.
    
    This class uses trough detection on ball height data to segment
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
        normalized_data_list: list[dict],
        fps: float
    ) -> list[list[dict]]:
        """
        Detects individual dribble cycles by finding troughs in ball height.

        Uses SciPy's find_peaks to identify local maxima in the ball's
        vertical position (lowest point of the dribble). The frames between
        consecutive troughs represent one complete dribble cycle.
        
        Args:
            normalized_data_list: List of valid normalized frame dictionaries.
            fps: Frames per second of the video.
        
        Returns:
            List of dribble cycles, where each cycle is a list of frame data.
        """
        print("Detecting dribble cycles...")
        
        ball_heights = []
        valid_indices = []

        for idx, frame in enumerate(normalized_data_list):
            if frame.get('ball_center'):
                ball_heights.append(frame['ball_center'][1])
                valid_indices.append(idx)
            else:
                ball_heights.append(None)

        valid_heights = [h for h in ball_heights if h is not None]
        
        if len(valid_heights) < self.min_cycle_duration:
            print(f"  Not enough valid data points ({len(valid_heights)}) for cycle detection")
            return []
        
        peaks, properties = find_peaks(
            valid_heights,
            distance=self.min_cycle_duration,
            prominence=0.1
        )
        
        peak_frame_indices = [valid_indices[p] for p in peaks]
        
        print(f"  Found {len(peak_frame_indices)} troughs (dribble cycle markers)")
        print(f"  Trough frames: {peak_frame_indices}")
        
        dribble_cycles = []
        
        for i in range(len(peak_frame_indices) - 1):
            start_idx = peak_frame_indices[i]
            end_idx = peak_frame_indices[i + 1]

            cycle_frames = normalized_data_list[start_idx:end_idx]

            if len(cycle_frames) >= self.min_cycle_duration:
                dribble_cycles.append(cycle_frames)
                duration_ms = cycle_frames[-1]['timestamp_ms'] - cycle_frames[0]['timestamp_ms']
                print(
                    f"  Cycle {len(dribble_cycles)}: {len(cycle_frames)} frames ({duration_ms}ms)"
                )
        
        print(f"  Total dribble cycles detected: {len(dribble_cycles)}")
        
        return dribble_cycles
