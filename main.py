import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import cv2

path_to_object_detection_model = "models/efficientdet_lite0.tflite"
path_to_reference_video = "videos/reference.mov"

import mediapipe as mp

BaseOptions = mp.tasks.BaseOptions
ObjectDetector = mp.tasks.vision.ObjectDetector
ObjectDetectorOptions = mp.tasks.vision.ObjectDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = ObjectDetectorOptions(
    base_options=BaseOptions(model_asset_path=path_to_object_detection_model),
    max_results=1, # Maximum number of detections (objects) to return (in our case, basketballs)
    running_mode=VisionRunningMode.VIDEO)

with ObjectDetector.create_from_options(options) as detector: # Detector is the detector instance we create using our options (we're now accessing it)
  cap = cv2.VideoCapture(path_to_reference_video) # Capture video from the reference video file
  fps = cap.get(cv2.CAP_PROP_FPS)
  frame_index = 0
  
  while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Ignoring empty camera frame.")
        continue

    time = int(frame_index / fps * 1000) # Calculate timestamp in milliseconds

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    result = detector.detect_for_video(mp_image, time)

    print(result)

    frame_index += 1