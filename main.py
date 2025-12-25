import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
import numpy as np

path_to_object_detection_model = "models/efficientdet_lite0.tflite"
path_to_pose_model = "models/pose_landmarker_full.task"
path_to_reference_video = "videos/reference.mov"

BaseOptions = mp.tasks.BaseOptions
ObjectDetector = mp.tasks.vision.ObjectDetector
ObjectDetectorOptions = mp.tasks.vision.ObjectDetectorOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

DETECT_EVERY_N_FRAMES = 10


def create_detector():
    """
    Creates and configures a MediaPipe ObjectDetector for basketball detection.
    
    Returns:
        ObjectDetector: Configured detector instance for video processing.
    """
    options = ObjectDetectorOptions(
        base_options=BaseOptions(model_asset_path=path_to_object_detection_model),
        max_results=1,
        score_threshold=0.3,
        category_allowlist=['sports ball'],
        running_mode=VisionRunningMode.VIDEO)
    return ObjectDetector.create_from_options(options)


def detect_ball(detector, frame, timestamp_ms):
    """
    Detects basketball in a video frame using MediaPipe object detection.
    
    Args:
        detector: MediaPipe ObjectDetector instance.
        frame: Video frame as numpy array (BGR format).
        timestamp_ms: Frame timestamp in milliseconds.
    
    Returns:
        tuple: (x, y, w, h) bounding box coordinates, or None if no ball detected.
    """
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    result = detector.detect_for_video(mp_image, timestamp_ms)
    
    if result.detections:
        detection = result.detections[0]
        bounding_box = detection.bounding_box
        
        x = int(bounding_box.origin_x)
        y = int(bounding_box.origin_y)
        w = int(bounding_box.width)
        h = int(bounding_box.height)
        
        return (x, y, w, h)
    return None


def track_ball(tracker, frame):
    """
    Tracks basketball using OpenCV tracker.
    
    Args:
        tracker: OpenCV tracker instance (e.g., TrackerCSRT).
        frame: Video frame as numpy array (BGR format).
    
    Returns:
        tuple: (x, y, w, h) bounding box coordinates, or None if tracking failed.
    """
    success, bbox = tracker.update(frame)
    if success:
        x, y, w, h = [int(v) for v in bbox]
        return (x, y, w, h)
    return None


def draw_bounding_box(frame, bbox, color, label):
    """
    Draws a bounding box with label on a video frame.
    
    Args:
        frame: Video frame to draw on (modified in-place).
        bbox: Tuple of (x, y, w, h) bounding box coordinates.
        color: BGR color tuple for the box and text.
        label: String label to display above the box.
    
    Returns:
        None
    """
    x, y, w, h = bbox
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    cv2.putText(frame, label, (x, y - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def draw_ball_center(frame, center):
    """
    Draws a red dot at the ball's center position.
    
    Args:
        frame: Video frame to draw on (modified in-place).
        center: Tuple of (x, y) center coordinates.
    
    Returns:
        None
    """
    cv2.circle(frame, center, 5, (0, 0, 255), -1)


def draw_info(frame, frame_index, method, frames_since_detection):
    """
    Draws debug information on the video frame.
    
    Args:
        frame: Video frame to draw on (modified in-place).
        frame_index: Current frame number.
        method: String describing detection/tracking method used.
        frames_since_detection: Number of frames since last detection.
    
    Returns:
        None
    """
    cv2.putText(frame, f"Frame: {frame_index}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Method: {method}", (10, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Frames since detect: {frames_since_detection}", (10, 90),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)


def draw_ball_lost(frame):
    """
    Draws "BALL LOST" message on the video frame.
    
    Args:
        frame: Video frame to draw on (modified in-place).
    
    Returns:
        None
    """
    cv2.putText(frame, "BALL LOST", (50, 50),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)


def apply_orange_mask(frame):
    """
    Applies color masking to isolate orange objects (basketball) in the frame.
    
    Args:
        frame: Video frame as numpy array (BGR format).
    
    Returns:
        numpy.ndarray: Masked frame showing only orange-colored regions.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_orange = np.array([5, 100, 100])
    upper_orange = np.array([20, 255, 255])
    mask = cv2.inRange(hsv, lower_orange, upper_orange)
    masked_frame = cv2.bitwise_and(frame, frame, mask=mask)
    return masked_frame


def detect_pose(landmarker, frame, timestamp_ms):
    """
    Detects human pose landmarks in a frame using MediaPipe PoseLandmarker.
    
    Args:
        landmarker: MediaPipe PoseLandmarker instance.
        frame: Video frame as numpy array (BGR format).
        timestamp_ms: Timestamp of the frame in milliseconds.
    
    Returns:
        dict: Dictionary containing landmark positions or None if no pose detected.
              Keys: 'left_wrist', 'right_wrist', 'left_elbow', 'right_elbow',
                    'left_shoulder', 'right_shoulder', 'left_hip', 'right_hip',
                    'left_knee', 'right_knee', 'hip_center'
    """
    # Convert BGR to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Create MediaPipe Image
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    
    # Detect pose landmarks
    results = landmarker.detect_for_video(mp_image, timestamp_ms)
    
    if not results.pose_landmarks or len(results.pose_landmarks) == 0:
        return None
    
    # Get first pose (we only track one person)
    landmarks = results.pose_landmarks[0]
    h, w = frame.shape[:2]
    
    # MediaPipe Pose landmark indices (same as the old API)
    # 0: nose, 11: left_shoulder, 12: right_shoulder, 13: left_elbow, 14: right_elbow,
    # 15: left_wrist, 16: right_wrist, 23: left_hip, 24: right_hip, 25: left_knee, 26: right_knee
    left_wrist = landmarks[15]
    right_wrist = landmarks[16]
    left_elbow = landmarks[13]
    right_elbow = landmarks[14]
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    left_hip = landmarks[23]
    right_hip = landmarks[24]
    left_knee = landmarks[25]
    right_knee = landmarks[26]
    
    hip_center_x = (left_hip.x + right_hip.x) / 2
    hip_center_y = (left_hip.y + right_hip.y) / 2
    
    return {
        'left_wrist': (int(left_wrist.x * w), int(left_wrist.y * h)),
        'right_wrist': (int(right_wrist.x * w), int(right_wrist.y * h)),
        'left_elbow': (int(left_elbow.x * w), int(left_elbow.y * h)),
        'right_elbow': (int(right_elbow.x * w), int(right_elbow.y * h)),
        'left_shoulder': (int(left_shoulder.x * w), int(left_shoulder.y * h)),
        'right_shoulder': (int(right_shoulder.x * w), int(right_shoulder.y * h)),
        'left_hip': (int(left_hip.x * w), int(left_hip.y * h)),
        'right_hip': (int(right_hip.x * w), int(right_hip.y * h)),
        'left_knee': (int(left_knee.x * w), int(left_knee.y * h)),
        'right_knee': (int(right_knee.x * w), int(right_knee.y * h)),
        'hip_center': (int(hip_center_x * w), int(hip_center_y * h))
    }


def draw_pose_landmarks(frame, pose_data):
    """
    Draws circles and labels for detected pose landmarks.
    
    Args:
        frame: Video frame to draw on (modified in-place).
        pose_data: Dictionary of landmark positions from detect_pose().
    
    Returns:
        None
    """
    if not pose_data:
        return
    
    for name, pos in pose_data.items():
        cv2.circle(frame, pos, 5, (0, 255, 0), -1)
        cv2.putText(frame, name, (pos[0] + 10, pos[1]), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)


def process_video():
    """
    Main function to process video with hybrid ball detection and tracking.
    
    Uses MediaPipe object detection and OpenCV tracking to locate and follow
    a basketball throughout the video. Applies orange color masking to improve
    detection accuracy. Displays the processed video with bounding boxes and
    tracking information overlayed.
    
    Returns:
        None
    """
    # Create pose landmarker options
    pose_options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=path_to_pose_model),
        running_mode=VisionRunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    with create_detector() as detector, \
         PoseLandmarker.create_from_options(pose_options) as pose_landmarker:
        cap = cv2.VideoCapture(path_to_reference_video)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_index = 0
        
        tracker = None
        tracking_active = False
        frames_since_detection = 0
        
        print(f"Starting video processing...")
        print(f"Video FPS: {fps}")
        print(f"Will detect every {DETECT_EVERY_N_FRAMES} frames")
        print("-" * 50)
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("End of video reached")
                break

            original_frame = frame.copy()
            masked_frame = apply_orange_mask(frame)

            timestamp_ms = int(frame_index / fps * 1000)
            
            ball_center = None
            method_used = None
            
            should_detect = (
                not tracking_active or
                frames_since_detection >= DETECT_EVERY_N_FRAMES
            )
            
            if should_detect:
                bbox = detect_ball(detector, original_frame, timestamp_ms)
                
                if bbox:
                    x, y, w, h = bbox
                    ball_center = (x + w // 2, y + h // 2)
                    
                    tracker = cv2.legacy.TrackerCSRT_create()
                    tracker.init(masked_frame, bbox)
                    tracking_active = True
                    frames_since_detection = 0
                    method_used = "detection"
                    
                    draw_bounding_box(original_frame, bbox, (0, 255, 0), "DETECT")
                    
                elif tracking_active:
                    bbox = track_ball(tracker, masked_frame)
                    
                    if bbox:
                        x, y, w, h = bbox
                        ball_center = (x + w // 2, y + h // 2)
                        frames_since_detection += 1
                        method_used = "tracking_fallback"
                        
                        draw_bounding_box(original_frame, bbox, (0, 165, 255), "TRACK (FB)")
                    else:
                        tracking_active = False
                        method_used = "lost"
                else:
                    method_used = "lost"
            
            else:
                bbox = track_ball(tracker, masked_frame)
                
                if bbox:
                    x, y, w, h = bbox
                    ball_center = (x + w // 2, y + h // 2)
                    frames_since_detection += 1
                    method_used = "tracking"
                    
                    draw_bounding_box(original_frame, bbox, (255, 0, 0), "TRACK")
                else:
                    tracking_active = False
                    frames_since_detection = DETECT_EVERY_N_FRAMES
                    method_used = "lost"
            
            if ball_center:
                draw_ball_center(original_frame, ball_center)
            else:
                draw_ball_lost(original_frame)
            
            # Detect and draw pose landmarks
            timestamp_ms = int((frame_index / fps) * 1000)
            pose_data = detect_pose(pose_landmarker, original_frame, timestamp_ms)
            if pose_data:
                draw_pose_landmarks(original_frame, pose_data)
            
            draw_info(original_frame, frame_index, method_used, frames_since_detection)
            
            frame_index += 1
            
            cv2.imshow('Hybrid Ball Tracking', original_frame)
            if cv2.waitKey(5) & 0xFF == 27:
                break
        
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    process_video()
