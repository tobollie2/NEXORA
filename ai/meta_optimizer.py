# ai/meta_optimizer.py
from typing import Any, Dict

import numpy as np


class MetaOptimizationController:
    """
    Coordinates multiple sub-agents by adjusting hyperparameters
    based on aggregate performance feedback. This enables
    adaptive tuning of exploration, learning rate, and agent weights.
    """

    def __init__(self, config: Dict[str, Any]):
        self.lr = config.get("meta_lr", 0.05)
        self.momentum = config.get("momentum", 0.8)
        self.prev_grad = {}
        self.performance_history: Dict[str, list] = {}

    def update(
        self, agent_metrics: Dict[str, Dict[str, float]], global_reward: float
    ) -> Dict[str, Dict[str, float]]:
        """
        Takes per-agent metrics and global performance, returns
        updated hyperparameters for each agent.
        """
        updated_params = {}

        for name, metrics in agent_metrics.items():
            reward = metrics.get("reward", 0.0)
            sharpe = metrics.get("sharpe", 0.0)
            vol = metrics.get("volatility", 1e-8)

            # Composite performance score
            perf = reward * (sharpe / (vol + 1e-6))

            # Track performance over time
            self.performance_history.setdefault(name, []).append(perf)
            hist = np.array(self.performance_history[name][-10:])
            grad = np.mean(np.diff(hist)) if len(hist) > 1 else 0.0

            # Smooth updates
            grad = self.momentum * self.prev_grad.get(name, 0.0) + (1 - self.momentum) * grad
            self.prev_grad[name] = grad

            # Adjust hyperparameters
            new_lr = np.clip(metrics.get("lr", 0.01) * (1 + self.lr * grad), 1e-5, 0.1)
            new_eps = np.clip(metrics.get("epsilon", 0.3) * (1 - 0.5 * grad), 0.05, 0.9)
            weight = np.clip(1 + grad, 0.5, 2.0)

            updated_params[name] = {
                "lr": new_lr,
                "epsilon": new_eps,
                "weight": weight,
            }

        return updated_params
