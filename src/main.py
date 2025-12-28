"""Main video processing module with VideoProcessor orchestrator."""

import cv2
from typing import Optional

from config import Config
from detectors.ball_detector import BallDetector
from detectors.pose_detector import PoseDetector
from trackers.ball_tracker import BallTracker
from processors.data_cleaner import DataCleaner
from processors.normalizer import CoordinateNormalizer
from processors.cycle_detector import CycleDetector
from visualizers.frame_visualizer import FrameVisualizer
from utils.video_utils import apply_orange_mask


class VideoProcessor:
    """
    Video processor that orchestrates all components for basketball tracking.
    
    This class coordinates ball detection, tracking, pose detection, data
    cleaning, normalization, and visualization to process basketball videos.
    
    Attributes:
        config: Configuration object with all parameters.
        ball_detector: Ball detection component.
        pose_detector: Pose detection component.
        ball_tracker: Ball tracking component.
        data_cleaner: Data cleaning component.
        normalizer: Coordinate normalization component.
        cycle_detector: Dribble cycle detection component.
        visualizer: Frame visualization component.
        frame_data_list: List to store raw detection data from each frame.
    """
    
    def __init__(self, config: Config):
        """
        Initializes the VideoProcessor.
        
        Args:
            config: Config object containing all paths and parameters.
        """
        self.config = config
        self.ball_detector = BallDetector(config)
        self.pose_detector = PoseDetector(config)
        self.ball_tracker = BallTracker()
        self.data_cleaner = DataCleaner(config.max_velocity)
        self.normalizer = CoordinateNormalizer()
        self.cycle_detector = CycleDetector(config.min_cycle_duration)
        self.visualizer = FrameVisualizer()
        self.frame_data_list: list[dict] = []
    
    def _process_frame(
        self, 
        frame: cv2.Mat, 
        frame_index: int, 
        fps: float, 
        frames_since_detection: int
    ) -> tuple[Optional[tuple[int, int]], str, int]:
        """
        Processes a single video frame for ball detection and tracking.
        
        Args:
            frame: Video frame to process.
            frame_index: Current frame number.
            fps: Frames per second of the video.
            frames_since_detection: Number of frames since last detection.
        
        Returns:
            Tuple of (ball_center, method_used, updated_frames_since_detection).
        """
        original_frame = frame.copy()
        masked_frame = apply_orange_mask(
            frame, 
            self.config.orange_mask_lower, 
            self.config.orange_mask_upper
        )
        
        timestamp_ms = int(frame_index / fps * 1000)
        ball_center = None
        method_used = None
        
        should_detect = (
            not self.ball_tracker.is_active() or
            frames_since_detection >= self.config.detect_every_n_frames
        )
        
        if should_detect:
            bbox = self.ball_detector.detect(original_frame, timestamp_ms)
            
            if bbox:
                x, y, w, h = bbox
                ball_center = (x + w // 2, y + h // 2)
                
                self.ball_tracker.initialize(masked_frame, bbox)
                frames_since_detection = 0
                method_used = "detection"
                
                self.visualizer.draw_bounding_box(
                    original_frame, bbox, (0, 255, 0), "DETECT"
                )
                
            elif self.ball_tracker.is_active():
                bbox = self.ball_tracker.update(masked_frame)
                
                if bbox:
                    x, y, w, h = bbox
                    ball_center = (x + w // 2, y + h // 2)
                    frames_since_detection += 1
                    method_used = "tracking_fallback"
                    
                    self.visualizer.draw_bounding_box(
                        original_frame, bbox, (0, 165, 255), "TRACK (FB)"
                    )
                else:
                    method_used = "lost"
            else:
                method_used = "lost"
        
        else:
            bbox = self.ball_tracker.update(masked_frame)
            
            if bbox:
                x, y, w, h = bbox
                ball_center = (x + w // 2, y + h // 2)
                frames_since_detection += 1
                method_used = "tracking"
                
                self.visualizer.draw_bounding_box(
                    original_frame, bbox, (255, 0, 0), "TRACK"
                )
            else:
                self.ball_tracker.reset()
                frames_since_detection = self.config.detect_every_n_frames
                method_used = "lost"
        
        if ball_center:
            self.visualizer.draw_ball_center(original_frame, ball_center)
        else:
            self.visualizer.draw_ball_lost(original_frame)
        
        pose_data = self.pose_detector.detect(original_frame, timestamp_ms)
        if pose_data:
            self.visualizer.draw_pose_landmarks(original_frame, pose_data)
        
        frame_data = {
            'frame_index': frame_index,
            'timestamp_ms': timestamp_ms,
            'ball_center': ball_center,
            'left_wrist': pose_data.get('left_wrist') if pose_data else None,
            'right_wrist': pose_data.get('right_wrist') if pose_data else None,
            'left_elbow': pose_data.get('left_elbow') if pose_data else None,
            'right_elbow': pose_data.get('right_elbow') if pose_data else None,
            'left_shoulder': pose_data.get('left_shoulder') if pose_data else None,
            'right_shoulder': pose_data.get('right_shoulder') if pose_data else None,
            'left_knee': pose_data.get('left_knee') if pose_data else None,
            'right_knee': pose_data.get('right_knee') if pose_data else None,
            'hip_center': pose_data.get('hip_center') if pose_data else None
        }
        self.frame_data_list.append(frame_data)
        
        self.visualizer.draw_info(
            original_frame, frame_index, method_used, frames_since_detection
        )
        
        cv2.imshow('Hybrid Ball Tracking', original_frame)
        
        return ball_center, method_used, frames_since_detection
    
    def process(self) -> None:
        """
        Main method to process video with hybrid ball detection and tracking.
        
        Uses MediaPipe object detection and OpenCV tracking to locate and follow
        a basketball throughout the video. Applies orange color masking to improve
        detection accuracy. Displays the processed video with bounding boxes and
        tracking information overlayed.
        """
        with self.ball_detector, self.pose_detector:
            cap = cv2.VideoCapture(self.config.reference_video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_index = 0
            frames_since_detection = 0
            
            print(f"Starting video processing...")
            print(f"Video FPS: {fps}")
            print(f"Will detect every {self.config.detect_every_n_frames} frames")
            print("-" * 50)
            
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    print("End of video reached")
                    break
                
                _, _, frames_since_detection = self._process_frame(
                    frame, frame_index, fps, frames_since_detection
                )
                
                frame_index += 1
                
                if cv2.waitKey(5) & 0xFF == 27:
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            print("-" * 50)
            print(f"Processing complete! Collected data from {len(self.frame_data_list)} frames.")
            
            self.frame_data_list = self.data_cleaner.clean(self.frame_data_list)
            
            normalized_data_list = self.normalizer.normalize(self.frame_data_list)
            
            dribble_cycles = self.cycle_detector.detect_cycles(normalized_data_list, fps)
            
            print("-" * 50)
            print(f"Final normalized dataset: {sum(1 for x in normalized_data_list if x is not None)} valid frames")
            print(f"Detected {len(dribble_cycles)} complete dribble cycles")
            print("-" * 50)


def main() -> None:
    """Main entry point for video processing."""
    config = Config()
    processor = VideoProcessor(config)
    processor.process()


if __name__ == "__main__":
    main()
