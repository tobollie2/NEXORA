# /ai/temporal_memory.py
from collections import defaultdict, deque
from datetime import datetime

import numpy as np


class TemporalMemory:
    """
    Stores regime transitions, durations, and historical strategy performance.
    Enables context drift detection and anticipatory allocation adjustments.
    """

    def __init__(self, capacity=5000):
        self.memory = deque(maxlen=capacity)
        self.transition_counts = defaultdict(lambda: defaultdict(int))
        self.regime_durations = defaultdict(list)
        self.last_regime = None
        self.last_change = None
        self.performance_log = defaultdict(lambda: defaultdict(list))

    def record(self, regime: str, rewards: dict):
        """
        Record the current regime, strategy rewards, and handle transitions.
        """
        now = datetime.utcnow()
        self.memory.append({"time": now, "regime": regime, "rewards": rewards})

        # Record strategy performance under this regime
        for strat, reward in rewards.items():
            self.performance_log[regime][strat].append(reward)

        # Detect transitions
        if self.last_regime and regime != self.last_regime:
            self.transition_counts[self.last_regime][regime] += 1
            if self.last_change:
                duration = (now - self.last_change).total_seconds() / 3600  # in hours
                self.regime_durations[self.last_regime].append(duration)
            self.last_change = now
        elif self.last_regime is None:
            self.last_change = now

        self.last_regime = regime

    def average_duration(self, regime: str) -> float:
        if self.regime_durations[regime]:
            return float(np.mean(self.regime_durations[regime]))
        return float("nan")

    def transition_probabilities(self) -> dict:
        """Normalized transition matrix."""
        probs = {}
        for from_reg, to_dict in self.transition_counts.items():
            total = sum(to_dict.values())
            probs[from_reg] = {to: c / total for to, c in to_dict.items()}
        return probs

    def best_strategies_per_regime(self) -> dict:
        """Return average performance of strategies per regime."""
        return {
            reg: {s: np.mean(v) for s, v in strat_dict.items()}
            for reg, strat_dict in self.performance_log.items()
        }

    def detect_context_drift(self, current_regime: str, threshold=0.3) -> bool:
        """
        Detect regime behavior drift — if transition probabilities or durations deviate significantly.
        """
        probs = self.transition_probabilities()
        if current_regime not in probs:
            return False

        recent_transitions = len(self.regime_durations[current_regime])
        if recent_transitions < 3:
            return False

        avg_dur = np.mean(self.regime_durations[current_regime][-3:])
        long_dur = np.mean(self.regime_durations[current_regime])
        deviation = abs(avg_dur - long_dur) / (long_dur + 1e-8)

        return bool(deviation > threshold)
