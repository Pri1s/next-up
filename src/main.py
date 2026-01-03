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
from processors.contact_labeler import ContactLabeler
from processors.cycle_metrics import CycleMetrics
from processors.session_aggregator import SessionAggregator
from visualizers.frame_visualizer import FrameVisualizer
from utils.video_utils import (
    apply_orange_mask,
    bbox_area_ratio,
    bbox_orange_ratio,
    bbox_iou
)


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
        self.contact_labeler = ContactLabeler(
            k=config.contact_threshold_k,
            min_window_frames=config.min_contact_window_frames
        )
        self.cycle_metrics = None
        self.session_aggregator = SessionAggregator(
            crossover_hand_gap_tolerance=config.crossover_hand_gap_tolerance
        )
        self.visualizer = FrameVisualizer()
        self.frame_data_list: list[dict] = []
        self.recent_ball_centers: list[tuple[int, int]] = []
        self.force_detect_frames: int = 0
        self.grace_frames_left: int = 0
        self.last_good_ball_center: Optional[tuple[int, int]] = None

    def _log_rejection(
        self,
        frame_index: int,
        timestamp_ms: int,
        reason: str
    ) -> None:
        print(f"[REJECT] frame={frame_index} ts_ms={timestamp_ms} reason={reason}")

    def _bbox_passes_checks(
        self,
        frame: cv2.Mat,
        masked_frame: cv2.Mat,
        bbox: tuple[int, int, int, int]
    ) -> bool:
        area_ratio = bbox_area_ratio(bbox, frame.shape)
        if (
            area_ratio < self.config.min_ball_area_ratio or
            area_ratio > self.config.max_ball_area_ratio
        ):
            return False
        orange_ratio = bbox_orange_ratio(masked_frame, bbox)
        return orange_ratio >= self.config.min_orange_ratio

    def _passes_motion_gate(self, ball_center: tuple[int, int]) -> bool:
        if len(self.recent_ball_centers) < 2:
            return True
        prev = self.recent_ball_centers[-1]
        prev_prev = self.recent_ball_centers[-2]
        v1x = prev[0] - prev_prev[0]
        v1y = prev[1] - prev_prev[1]
        v2x = ball_center[0] - prev[0]
        v2y = ball_center[1] - prev[1]
        accel = ((v2x - v1x) ** 2 + (v2y - v1y) ** 2) ** 0.5
        return accel <= self.config.max_track_acceleration

    def _use_grace_center(self) -> Optional[tuple[int, int]]:
        if self.config.tracking_grace_frames <= 0:
            return None
        if self.last_good_ball_center is None:
            return None
        if self.grace_frames_left <= 0:
            self.grace_frames_left = self.config.tracking_grace_frames
        if self.grace_frames_left <= 0:
            return None
        self.grace_frames_left -= 1
        return self.last_good_ball_center
    
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
        if self.force_detect_frames > 0:
            should_detect = True
            self.force_detect_frames -= 1
        
        if should_detect:
            bbox = self.ball_detector.detect(original_frame, timestamp_ms)
            if bbox and not self._bbox_passes_checks(original_frame, masked_frame, bbox):
                self._log_rejection(frame_index, timestamp_ms, "detect_bbox_checks")
                bbox = None
            
            if bbox:
                if self.ball_tracker.is_active() and self.ball_tracker.last_bbox:
                    iou = bbox_iou(bbox, self.ball_tracker.last_bbox)
                    if iou < self.config.min_detect_track_iou:
                        self.force_detect_frames = max(
                            self.force_detect_frames, self.config.force_detect_frames
                        )
                        method_used = "detection_reinit"
                x, y, w, h = bbox
                ball_center = (x + w // 2, y + h // 2)
                
                self.ball_tracker.initialize(masked_frame, bbox)
                frames_since_detection = 0
                method_used = method_used or "detection"
                
                self.visualizer.draw_bounding_box(
                    original_frame, bbox, (0, 255, 0), "DETECT"
                )
                
            elif self.ball_tracker.is_active():
                bbox = self.ball_tracker.update(masked_frame)
                if bbox and not self._bbox_passes_checks(original_frame, masked_frame, bbox):
                    self._log_rejection(frame_index, timestamp_ms, "tracking_fallback_bbox_checks")
                    bbox = None
                
                if bbox:
                    x, y, w, h = bbox
                    ball_center = (x + w // 2, y + h // 2)
                    frames_since_detection += 1
                    method_used = "tracking_fallback"
                    
                    self.visualizer.draw_bounding_box(
                        original_frame, bbox, (0, 165, 255), "TRACK (FB)"
                    )
                else:
                    self.force_detect_frames = max(
                        self.force_detect_frames, self.config.force_detect_frames
                    )
                    grace_center = self._use_grace_center()
                    if grace_center:
                        ball_center = grace_center
                        frames_since_detection += 1
                        method_used = "tracking_grace"
                    else:
                        self.ball_tracker.reset()
                        method_used = "lost"
            else:
                method_used = "lost"
        
        else:
            bbox = self.ball_tracker.update(masked_frame)
            if bbox and not self._bbox_passes_checks(original_frame, masked_frame, bbox):
                self._log_rejection(frame_index, timestamp_ms, "tracking_bbox_checks")
                bbox = None
            
            if bbox:
                x, y, w, h = bbox
                ball_center = (x + w // 2, y + h // 2)
                frames_since_detection += 1
                method_used = "tracking"
                
                self.visualizer.draw_bounding_box(
                    original_frame, bbox, (255, 0, 0), "TRACK"
                )
            else:
                self.force_detect_frames = max(
                    self.force_detect_frames, self.config.force_detect_frames
                )
                grace_center = self._use_grace_center()
                if grace_center:
                    ball_center = grace_center
                    frames_since_detection += 1
                    method_used = "tracking_grace"
                else:
                    self.ball_tracker.reset()
                    frames_since_detection = self.config.detect_every_n_frames
                    method_used = "lost"

        if ball_center and method_used in {"tracking", "tracking_fallback"}:
            if not self._passes_motion_gate(ball_center):
                self._log_rejection(frame_index, timestamp_ms, "tracking_motion_gate")
                self.force_detect_frames = max(
                    self.force_detect_frames, self.config.force_detect_frames
                )
                grace_center = self._use_grace_center()
                if grace_center:
                    ball_center = grace_center
                    method_used = "tracking_grace"
                else:
                    ball_center = None
                    self.ball_tracker.reset()
                    frames_since_detection = self.config.detect_every_n_frames
                    method_used = "rejected_motion"
        
        if ball_center:
            self.visualizer.draw_ball_center(original_frame, ball_center)
            if method_used != "tracking_grace":
                self.last_good_ball_center = ball_center
                self.grace_frames_left = 0
                self.recent_ball_centers.append(ball_center)
                if len(self.recent_ball_centers) > 3:
                    self.recent_ball_centers.pop(0)
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
            valid_frames = [frame for frame in normalized_data_list if frame is not None]

            labeled_frames, shoulder_width_session = self.contact_labeler.label_frames(
                valid_frames
            )
            d_thr = self.config.contact_threshold_k * shoulder_width_session
            self.cycle_metrics = CycleMetrics(
                d_thr=d_thr,
                delta=self.config.dominant_hand_delta,
                min_window_frames=self.config.min_contact_window_frames
            )

            dribble_cycles = self.cycle_detector.detect_cycles(valid_frames, fps)

            labeled_by_frame = {frame.frame_index: frame for frame in labeled_frames}
            cycles = []
            for cycle_id, cycle_frames in enumerate(dribble_cycles):
                labeled_cycle_frames = [
                    labeled_by_frame[frame["frame_index"]]
                    for frame in cycle_frames
                    if frame["frame_index"] in labeled_by_frame
                ]
                if labeled_cycle_frames:
                    cycles.append(
                        self.cycle_metrics.compute_cycle_metrics(
                            labeled_cycle_frames, cycle_id
                        )
                    )

            summary = self.session_aggregator.compute_session_summary(
                cycles=cycles,
                total_frames=len(self.frame_data_list),
                valid_frames=len(valid_frames),
                shoulder_width_session=shoulder_width_session,
                d_thr=d_thr
            )

            print("-" * 50)
            print(
                f"Final normalized dataset: {len(valid_frames)} valid frames"
            )
            print(f"Detected {len(dribble_cycles)} complete dribble cycles")
            print("-" * 50)
            print("Session Summary:")
            print(f"  Total cycles: {len(summary.cycles)}")
            print(f"  Avg duration: {summary.duration_mean:.1f}ms")
            print(f"  Duration variance: {summary.duration_variance:.2f}")
            print(f"  Max height mean: {summary.max_height_mean:.3f}")
            print(f"  Controlled time ratio mean: {summary.controlled_time_ratio_mean:.3f}")
            print(f"  Control deviation mean: {summary.control_deviation_mean:.4f}")
            print(f"  Crossovers: {summary.crossovers_count}")
            print(
                f"  Hand ratios (L/R): {summary.left_hand_ratio:.2f} / {summary.right_hand_ratio:.2f}"
            )
            print("-" * 50)


def main() -> None:
    """Main entry point for video processing."""
    config = Config()
    processor = VideoProcessor(config)
    processor.process()


if __name__ == "__main__":
    main()
