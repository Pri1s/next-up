"""Contact labeler module for per-frame hand contact labeling."""

from statistics import median
from typing import Optional

from models.labeled_frame import LabeledFrame


class ContactLabeler:
    """
    Contact labeler for identifying hand contact per frame.

    Computes a session-level control threshold using shoulder width, then
    labels each frame as L, R, None, or unknown based on ball-wrist distance.
    """

    def __init__(self, k: float = 0.5, min_window_frames: int = 3):
        """
        Initializes the ContactLabeler.

        Args:
            k: Control threshold multiplier (d_thr = k * shoulder_width_session).
            min_window_frames: Minimum frames for a meaningful contact window.
        """
        self.k = k
        self.min_window_frames = min_window_frames

    @staticmethod
    def _distance(
        a: Optional[tuple[float, float]],
        b: Optional[tuple[float, float]]
    ) -> Optional[float]:
        if a is None or b is None:
            return None
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return (dx ** 2 + dy ** 2) ** 0.5

    def _compute_shoulder_width_session(
        self,
        normalized_frames: list[dict]
    ) -> float:
        widths = []
        for frame in normalized_frames:
            left = frame.get("left_shoulder")
            right = frame.get("right_shoulder")
            dist = self._distance(left, right)
            if dist is not None:
                widths.append(dist)
        return median(widths) if widths else 0.0

    def label_frames(
        self,
        normalized_frames: list[dict]
    ) -> tuple[list[LabeledFrame], float]:
        """
        Labels frames with hand contact and distances.

        Args:
            normalized_frames: Valid normalized frame dictionaries.

        Returns:
            Tuple of (labeled_frames, shoulder_width_session).
        """
        shoulder_width_session = self._compute_shoulder_width_session(normalized_frames)
        d_thr = self.k * shoulder_width_session

        labeled_frames: list[LabeledFrame] = []
        for frame in normalized_frames:
            ball_center = frame.get("ball_center")
            left_wrist = frame.get("left_wrist")
            right_wrist = frame.get("right_wrist")

            d_left = self._distance(ball_center, left_wrist)
            d_right = self._distance(ball_center, right_wrist)
            d_min = None
            if d_left is not None and d_right is not None:
                d_min = min(d_left, d_right)
            elif d_left is not None:
                d_min = d_left
            elif d_right is not None:
                d_min = d_right

            if ball_center is None or (left_wrist is None and right_wrist is None):
                contact_label = "unknown"
            elif d_left is None and d_right is None:
                contact_label = "unknown"
            else:
                if d_left is not None and d_left < d_thr and (
                    d_right is None or d_left <= d_right
                ):
                    contact_label = "L"
                elif d_right is not None and d_right < d_thr and (
                    d_left is None or d_right < d_left
                ):
                    contact_label = "R"
                else:
                    contact_label = "None"

            labeled_frames.append(
                LabeledFrame(
                    frame_index=frame["frame_index"],
                    timestamp_ms=frame["timestamp_ms"],
                    cycle_id=None,
                    contact_label=contact_label,
                    d_left=d_left,
                    d_right=d_right,
                    d_min=d_min,
                    ball_center=ball_center,
                    left_wrist=left_wrist,
                    right_wrist=right_wrist,
                    left_shoulder=frame.get("left_shoulder"),
                    right_shoulder=frame.get("right_shoulder"),
                    left_knee=frame.get("left_knee"),
                    right_knee=frame.get("right_knee"),
                    hip_center=frame.get("hip_center", (0.0, 0.0)),
                )
            )

        return labeled_frames, shoulder_width_session
