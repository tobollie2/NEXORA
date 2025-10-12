# /ai/agent_core.py
import random
from collections import deque
from typing import Any, Dict

import numpy as np


class AdaptiveAgent:
    """
    Reinforcement learning core for adaptive strategy tuning.
    Learns optimal parameter configurations based on backtest rewards.
    """

    def __init__(self, strategy_adapter, reward_fn, config):
        self.strategy_adapter = strategy_adapter
        self.reward_fn = reward_fn
        self.config = config
        self.memory = deque(maxlen=config.get("memory_size", 500))
        self.epsilon = config.get("epsilon", 0.3)  # Exploration rate
        self.lr = config.get("learning_rate", 0.01)
        self.gamma = config.get("gamma", 0.95)  # Discount factor
        self.best_params = None
        self.best_score = -np.inf

    def select_action(self, state):
        """Choose next action (parameter set) — exploration vs exploitation."""
        if random.random() < self.epsilon or not self.best_params:
            return self.strategy_adapter.sample_parameters()
        return self.best_params

    def observe(self, state, params, reward, next_state):
        """Store experience for learning."""
        self.memory.append((state, params, reward, next_state))

    def learn(self):
        """Simple Q-learning style parameter update."""
        if not self.memory:
            return

        state, params, reward, next_state = random.choice(self.memory)

        # Basic heuristic update (could evolve to neural approximation)
        score = reward
        if score > self.best_score:
            self.best_score = score
            self.best_params = params
            self.epsilon *= 0.99  # Gradually reduce exploration

    def run_episode(self, data):
        """Run one full backtest-episode to evaluate strategy fitness."""
        state = self.strategy_adapter.extract_features(data)
        params = self.select_action(state)
        results = self.strategy_adapter.run_backtest(params, data)
        reward = self.reward_fn(results)
        self.observe(state, params, reward, None)
        self.learn()
        return reward, params, None  # Add placeholder for 'loss'
