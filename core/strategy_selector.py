# File: core/strategy_selector.py

import importlib


class StrategySelector:
    """
    Loads and executes the appropriate strategy module based on detected regime.
    """

    def __init__(self, logger=None, config=None):
        self.logger = logger
        self.config = config or {}

        self.active_strategy = None
        self.strategy_map = {
            "TREND": "strategies.trend",
            "MEAN_REVERT": "strategies.mean_reversion",
            "VOLATILE": "strategies.stat_arb",
        }

    def load_strategy(self, regime_name: str):
        """
        Dynamically import and instantiate the appropriate strategy class.
        """
        module_path = self.strategy_map.get(regime_name)
        if not module_path:
            if self.logger:
                self.logger.warning(f"No strategy mapped for regime: {regime_name}")
            return None

        try:
            module = importlib.import_module(module_path)
            strategy_class = getattr(module, "Strategy")
            strategy_instance = strategy_class(logger=self.logger, config=self.config)
            self.active_strategy = strategy_instance
            if self.logger:
                self.logger.info(
                    f"🧭 Activated strategy: {strategy_class.__name__} ({regime_name})"
                )
            return strategy_instance
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load strategy for {regime_name}: {e}")
            return None

    def execute(self, features):
        """
        Execute the active strategy on the latest features.
        Returns trade signal(s).
        """
        if not self.active_strategy:
            if self.logger:
                self.logger.warning("No active strategy — cannot execute.")
            return []

        try:
            signals = self.active_strategy.generate_signals(features)
            if self.logger:
                self.logger.info(
                    f"Strategy {self.active_strategy.__class__.__name__} signals: {signals}"
                )
            return signals
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error executing strategy: {e}")
            return []
