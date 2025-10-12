# strategies/base_strategy.py
# pyright: strict
from __future__ import annotations
from typing import Any, Dict, Optional, Union
import pandas as pd


class BaseStrategy:
    """
    Base class for all NEXORA trading strategies.
    Provides configuration management, logging, and abstract methods for strategy execution.
    """

    # -------------------------------------------------------------------------
    def __init__(
        self, config: Optional[Dict[str, Any]] = None, logger: Optional[Any] = None
    ) -> None:
        """
        Initialize the base strategy.

        Args:
            config: Dictionary containing strategy-specific parameters.
            logger: Optional logger object for recording events.
        """
        self.config: Dict[str, Any] = config or {}
        self.logger = logger

    # -------------------------------------------------------------------------
    def get_param(
        self, key: str, default: Union[int, float, str, None] = None
    ) -> Union[int, float, str, None]:
        """
        Retrieve a typed configuration parameter safely.

        Args:
            key: Parameter key name.
            default: Fallback value if key not found or type invalid.

        Returns:
            A validated parameter value.
        """
        value = self.config.get(key, default)
        if isinstance(value, (int, float, str)):
            return value
        return default

    # -------------------------------------------------------------------------
    def log(self, message: str) -> None:
        """
        Send a log message either through the assigned logger or print fallback.
        """
        if self.logger is not None:
            try:
                self.logger.info(message)
            except Exception:
                print(f"[LOGGER ERROR] {message}")
        else:
            print(message)

    # -------------------------------------------------------------------------
    def generate_signal(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Abstract method to be implemented by subclasses.
        Should return a trading signal dictionary, e.g.:
        {"symbol": "BTC", "side": "BUY", "price": 27000.5}
        """
        raise NotImplementedError("generate_signal() must be implemented by subclass")

    # -------------------------------------------------------------------------
    def run_backtest(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Abstract method to be implemented by subclasses.
        Should return a summary of strategy performance metrics.
        Example:
            {
                "strategy": "TrendFollowing",
                "total_return": 0.12,
                "sharpe": 1.8
            }
        """
        raise NotImplementedError("run_backtest() must be implemented by subclass")

    # -------------------------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        """
        Return a basic configuration summary for logging or debugging.
        """
        return {"strategy": self.__class__.__name__, "parameters": self.config}
