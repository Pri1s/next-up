"""Session aggregation module for dribble cycle metrics."""

from statistics import mean, pvariance

from models.cycle import Cycle
from models.session_summary import SessionSummary


class SessionAggregator:
    """Aggregates cycle metrics into session-level statistics."""

    def __init__(self, crossover_hand_gap_tolerance: int = 0):
        self.crossover_hand_gap_tolerance = max(0, crossover_hand_gap_tolerance)

    @staticmethod
    def _stats(values: list[float]) -> tuple[float, float]:
        if not values:
            return 0.0, 0.0
        if len(values) == 1:
            return values[0], 0.0
        return mean(values), pvariance(values)

    def _count_crossovers(self, cycles: list[Cycle]) -> int:
        """
        Count crossover transitions between consecutive cycles.
        
        A crossover is when the cycle_hand changes from one cycle to the next,
        and both cycles have a known (non-None) cycle_hand.
        
        Args:
            cycles: List of cycles in order.
            
        Returns:
            Number of hand-change transitions between consecutive cycles.
        """
        crossovers = 0
        i = 0
        while i < len(cycles) - 1:
            hand_j = cycles[i].cycle_hand
            if hand_j is None:
                i += 1
                continue
            next_idx = None
            for offset in range(1, self.crossover_hand_gap_tolerance + 2):
                j = i + offset
                if j >= len(cycles):
                    break
                hand_j1 = cycles[j].cycle_hand
                if hand_j1 is not None:
                    next_idx = j
                    if hand_j1 != hand_j:
                        crossovers += 1
                    break
            if next_idx is None:
                i += 1
            else:
                i = next_idx
        return crossovers

    @staticmethod
    def _compute_hand_ratios(cycles: list[Cycle]) -> tuple[float, float, int]:
        """
        Compute left/right hand ratios from cycle_hand across all cycles.
        
        Args:
            cycles: List of cycles.
            
        Returns:
            Tuple of (left_ratio, right_ratio, sample_size).
        """
        hand_samples = [c.cycle_hand for c in cycles if c.cycle_hand in ("L", "R")]
        sample_size = len(hand_samples)
        if sample_size == 0:
            return 0.0, 0.0, 0
        left_count = sum(1 for h in hand_samples if h == "L")
        right_count = sample_size - left_count
        return left_count / sample_size, right_count / sample_size, sample_size

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

        # Crossovers now counted as hand-change transitions between consecutive cycles
        crossovers_count = self._count_crossovers(cycles)

        # Hand ratios computed from cycle_hand across all cycles with known hand
        left_ratio, right_ratio, sample_size = self._compute_hand_ratios(cycles)

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
