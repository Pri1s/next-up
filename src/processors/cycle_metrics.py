"""Cycle metrics computation module."""

from statistics import mean
from typing import Optional

from models.contact_event import ContactEvent
from models.cycle import Cycle
from models.labeled_frame import LabeledFrame


class CycleMetrics:
    """
    Computes per-cycle metrics from labeled frames.
    """

    def __init__(self, d_thr: float, delta: float = 0.1, min_window_frames: int = 3):
        """
        Initializes CycleMetrics.

        Args:
            d_thr: Control threshold distance for contact labeling reference.
            delta: Dominant hand margin threshold.
            min_window_frames: Minimum frames for a meaningful contact window.
        """
        self.d_thr = d_thr
        self.delta = delta
        self.min_window_frames = min_window_frames

    @staticmethod
    def _mean(values: list[float]) -> float:
        return mean(values) if values else 0.0

    def _group_contact_events(
        self,
        frames: list[LabeledFrame],
        start_time_ms: float,
        duration_ms: float
    ) -> list[ContactEvent]:
        contact_events: list[ContactEvent] = []
        current_hand: Optional[str] = None
        start_idx = 0

        for idx, frame in enumerate(frames):
            label = frame.contact_label
            if label not in ("L", "R"):
                if current_hand is not None:
                    contact_events.append(
                        self._build_contact_event(
                            frames,
                            current_hand,
                            start_idx,
                            idx - 1,
                            start_time_ms,
                            duration_ms,
                        )
                    )
                    current_hand = None
                continue

            if current_hand is None:
                current_hand = label
                start_idx = idx
            elif label != current_hand:
                contact_events.append(
                    self._build_contact_event(
                        frames,
                        current_hand,
                        start_idx,
                        idx - 1,
                        start_time_ms,
                        duration_ms,
                    )
                )
                current_hand = label
                start_idx = idx

        if current_hand is not None:
            contact_events.append(
                self._build_contact_event(
                    frames,
                    current_hand,
                    start_idx,
                    len(frames) - 1,
                    start_time_ms,
                    duration_ms,
                )
            )

        return contact_events

    @staticmethod
    def _build_contact_event(
        frames: list[LabeledFrame],
        hand: str,
        start_idx: int,
        end_idx: int,
        start_time_ms: float,
        duration_ms: float,
    ) -> ContactEvent:
        t_start_ms = frames[start_idx].timestamp_ms
        t_end_ms = frames[end_idx].timestamp_ms
        t_norm_start = None
        t_norm_end = None
        if duration_ms > 0:
            t_norm_start = (t_start_ms - start_time_ms) / duration_ms
            t_norm_end = (t_end_ms - start_time_ms) / duration_ms
        return ContactEvent(
            hand=hand,
            start_frame_index=frames[start_idx].frame_index,
            end_frame_index=frames[end_idx].frame_index,
            t_start_ms=t_start_ms,
            t_end_ms=t_end_ms,
            t_norm_start=t_norm_start,
            t_norm_end=t_norm_end,
        )

    def _contact_time_fractions(
        self,
        frames: list[LabeledFrame]
    ) -> tuple[float, float, float]:
        total_frames = len(frames)
        if total_frames == 0:
            return 0.0, 0.0, 0.0
        left_frames = sum(1 for f in frames if f.contact_label == "L")
        right_frames = sum(1 for f in frames if f.contact_label == "R")
        controlled_frames = left_frames + right_frames
        return (
            left_frames / total_frames,
            right_frames / total_frames,
            controlled_frames / total_frames,
        )

    def _hand_fields(
        self,
        contact_events: list[ContactEvent],
        contact_time_fraction_left: float,
        contact_time_fraction_right: float,
    ) -> tuple[Optional[str], Optional[str], Optional[bool], Optional[str]]:
        meaningful_events = [
            event for event in contact_events
            if event.frame_count >= self.min_window_frames
        ]
        start_hand = meaningful_events[0].hand if meaningful_events else None
        end_hand = meaningful_events[-1].hand if meaningful_events else None

        is_crossover = None
        if start_hand is not None and end_hand is not None:
            is_crossover = start_hand != end_hand

        dominant_hand = None
        if contact_time_fraction_left >= contact_time_fraction_right + self.delta:
            dominant_hand = "L"
        elif contact_time_fraction_right >= contact_time_fraction_left + self.delta:
            dominant_hand = "R"

        return start_hand, end_hand, is_crossover, dominant_hand

    def _switch_time_norm(
        self,
        contact_events: list[ContactEvent],
        start_hand: Optional[str],
        end_hand: Optional[str],
        start_time_ms: float,
        duration_ms: float,
    ) -> Optional[float]:
        if (
            start_hand is None
            or end_hand is None
            or start_hand == end_hand
            or duration_ms <= 0
        ):
            return None

        last_start_event = None
        for event in contact_events:
            if event.hand == start_hand:
                last_start_event = event

        first_end_event = None
        if last_start_event is not None:
            for event in contact_events:
                if (
                    event.hand == end_hand
                    and event.t_start_ms >= last_start_event.t_end_ms
                ):
                    first_end_event = event
                    break

        if last_start_event is None or first_end_event is None:
            return None

        mid_time = (last_start_event.t_end_ms + first_end_event.t_start_ms) / 2
        return (mid_time - start_time_ms) / duration_ms

    @staticmethod
    def _control_deviation(
        frames: list[LabeledFrame]
    ) -> tuple[Optional[float], Optional[float]]:
        overall_values = [f.d_min for f in frames if f.d_min is not None]
        in_control_values = [
            f.d_min for f in frames
            if f.d_min is not None and f.contact_label in ("L", "R")
        ]
        overall = mean(overall_values) if overall_values else None
        in_control = mean(in_control_values) if in_control_values else None
        return overall, in_control

    def compute_cycle_metrics(
        self,
        frames: list[LabeledFrame],
        cycle_id: int
    ) -> Cycle:
        if not frames:
            raise ValueError("Cycle frames cannot be empty")

        for frame in frames:
            frame.cycle_id = cycle_id

        start_time_ms = frames[0].timestamp_ms
        end_time_ms = frames[-1].timestamp_ms
        duration_ms = end_time_ms - start_time_ms

        ball_heights = [
            frame.ball_center[1]
            for frame in frames
            if frame.ball_center is not None
        ]
        max_height = min(ball_heights) if ball_heights else 0.0
        min_height = max(ball_heights) if ball_heights else 0.0
        avg_height = self._mean(ball_heights)
        height_range = min_height - max_height

        contact_events = self._group_contact_events(
            frames, start_time_ms, duration_ms
        )

        (
            contact_time_fraction_left,
            contact_time_fraction_right,
            controlled_time_ratio,
        ) = self._contact_time_fractions(frames)

        start_hand, end_hand, is_crossover, dominant_hand = self._hand_fields(
            contact_events,
            contact_time_fraction_left,
            contact_time_fraction_right,
        )

        switch_time_norm = self._switch_time_norm(
            contact_events,
            start_hand,
            end_hand,
            start_time_ms,
            duration_ms,
        )

        control_deviation_overall, control_deviation_in_control = (
            self._control_deviation(frames)
        )

        return Cycle(
            cycle_id=cycle_id,
            frames=frames,
            contact_events=contact_events,
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
            duration_ms=duration_ms,
            max_height=max_height,
            min_height=min_height,
            avg_height=avg_height,
            height_range=height_range,
            contact_time_fraction_left=contact_time_fraction_left,
            contact_time_fraction_right=contact_time_fraction_right,
            controlled_time_ratio=controlled_time_ratio,
            start_hand=start_hand,
            end_hand=end_hand,
            is_crossover=is_crossover,
            dominant_hand=dominant_hand,
            switch_time_norm=switch_time_norm,
            control_deviation_overall=control_deviation_overall,
            control_deviation_in_control=control_deviation_in_control,
        )
