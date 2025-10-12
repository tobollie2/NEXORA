# /ai/strategy_adapter.py
import random


class StrategyAdapter:
    """Wraps a NEXORA strategy to make it tunable by the agent."""

    def __init__(self, strategy_cls, config):
        self.strategy_cls = strategy_cls
        self.config = config
        self.param_space = strategy_cls.parameter_grid()

    def sample_parameters(self):
        """Randomly pick parameter set from strategy’s grid."""
        return {k: random.choice(v) for k, v in self.param_space.items()}

    def extract_features(self, data):
        """Extracts normalized summary features (placeholder)."""
        return {"volatility": data["returns"].std(), "trend": data["returns"].mean()}

    def run_backtest(self, params, data):
        """Runs strategy with given parameters on data, returns results."""
        strategy = self.strategy_cls(params=params, config=self.config)
        return strategy.run_backtest(data)
