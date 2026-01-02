"""Session aggregation module for dribble cycle metrics."""

from statistics import mean, pvariance

from models.cycle import Cycle
from models.session_summary import SessionSummary


class SessionAggregator:
    """Aggregates cycle metrics into session-level statistics."""

    @staticmethod
    def _stats(values: list[float]) -> tuple[float, float]:
        if not values:
            return 0.0, 0.0
        if len(values) == 1:
            return values[0], 0.0
        return mean(values), pvariance(values)

    def compute_session_summary(
        self,
        cycles: list[Cycle],
        total_frames: int,
        valid_frames: int,
        shoulder_width_session: float,
        d_thr: float,
    ) -> SessionSummary:
        duration_values = [c.duration_ms for c in cycles]
        max_height_values = [c.max_height for c in cycles]
        controlled_values = [c.controlled_time_ratio for c in cycles]
        control_deviation_values = [
            c.control_deviation_in_control
            for c in cycles
            if c.control_deviation_in_control is not None
        ]

        duration_mean, duration_variance = self._stats(duration_values)
        max_height_mean, max_height_variance = self._stats(max_height_values)
        controlled_mean, controlled_variance = self._stats(controlled_values)
        control_mean, control_variance = self._stats(control_deviation_values)

        crossovers_count = sum(1 for c in cycles if c.is_crossover is True)

        hand_samples = []
        for c in cycles:
            if c.is_crossover is False:
                hand = c.dominant_hand or c.end_hand
                if hand in ("L", "R"):
                    hand_samples.append(hand)

        left_count = sum(1 for hand in hand_samples if hand == "L")
        right_count = sum(1 for hand in hand_samples if hand == "R")
        sample_size = len(hand_samples)
        if sample_size > 0:
            left_ratio = left_count / sample_size
            right_ratio = right_count / sample_size
        else:
            left_ratio = 0.0
            right_ratio = 0.0

        return SessionSummary(
            cycles=cycles,
            total_frames=total_frames,
            valid_frames=valid_frames,
            duration_mean=duration_mean,
            duration_variance=duration_variance,
            max_height_mean=max_height_mean,
            max_height_variance=max_height_variance,
            controlled_time_ratio_mean=controlled_mean,
            controlled_time_ratio_variance=controlled_variance,
            control_deviation_mean=control_mean,
            control_deviation_variance=control_variance,
            crossovers_count=crossovers_count,
            left_hand_ratio=left_ratio,
            right_hand_ratio=right_ratio,
            hand_ratio_sample_size=sample_size,
            shoulder_width_session=shoulder_width_session,
            d_thr=d_thr,
        )
