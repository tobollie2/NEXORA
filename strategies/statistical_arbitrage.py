# /strategies/statistical_arbitrage.py
import numpy as np
import pandas as pd
from statsmodels.api import OLS, add_constant
from statsmodels.tsa.stattools import coint

from strategies.base_strategy import BaseStrategy


class StatisticalArbitrageStrategy(BaseStrategy):
    """
    Adaptive Statistical-Arbitrage / Pairs-Trading Strategy
    -------------------------------------------------------
    Uses rolling Engle–Granger cointegration testing and dynamic
    hedge-ratio estimation to trade temporary deviations between
    two correlated assets.
    """

    def __init__(
        self,
        lookback: int = 100,
        entry_z: float = 2.0,
        exit_z: float = 0.5,
        coint_pval: float = 0.05,
        min_valid: int = 50,
    ):
        self.lookback = lookback
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.coint_pval = coint_pval
        self.min_valid = min_valid

    # ------------------------------------------------------------
    # Parameter Management
    # ------------------------------------------------------------
    def parameter_grid(self):
        return {
            "lookback": [60, 100, 150, 200],
            "entry_z": [1.5, 2.0, 2.5],
            "exit_z": [0.3, 0.5, 0.7],
            "coint_pval": [0.01, 0.05, 0.1],
        }

    def sample_parameters(self):
        return {
            "lookback": np.random.choice([60, 100, 150, 200]),
            "entry_z": np.random.uniform(1.5, 2.5),
            "exit_z": np.random.uniform(0.3, 0.7),
            "coint_pval": np.random.choice([0.01, 0.05, 0.1]),
        }

    # ------------------------------------------------------------
    # Core Backtest Logic
    # ------------------------------------------------------------
    def _rolling_beta(self, x: np.ndarray, y: np.ndarray, window: int):
        """Rolling OLS hedge-ratio β between x and y."""
        betas = np.full(len(x), np.nan)
        for i in range(window, len(x)):
            X = add_constant(x[i - window : i])
            model = OLS(y[i - window : i], X).fit()
            betas[i] = model.params[1]
        return pd.Series(betas, index=np.arange(len(x)))

    def run_backtest(self, params, data):
        lookback = params.get("lookback", self.lookback)
        entry_z = params.get("entry_z", self.entry_z)
        exit_z = params.get("exit_z", self.exit_z)
        coint_pval = params.get("coint_pval", self.coint_pval)

        x, y = data["X"]["close"].values, data["Y"]["close"].values
        if len(x) < self.min_valid:
            return {"total_return": 0.0, "sharpe": 0.0, "trades": 0}

        # --- Rolling β and spread
        beta = self._rolling_beta(x, y, lookback).ffill().bfill()
        spread = y - beta * x

        # --- Rolling mean/std of spread
        spread_mean = pd.Series(spread).rolling(lookback).mean()
        spread_std = pd.Series(spread).rolling(lookback).std()
        zscore = (spread - spread_mean) / spread_std

        # --- Rolling cointegration check
        pvals = []
        for i in range(lookback, len(x)):
            _, pval, _ = coint(x[i - lookback : i], y[i - lookback : i])
            pvals.append(pval)
        pvals = np.concatenate([np.full(lookback, np.nan), np.array(pvals)])
        coint_mask = pvals < coint_pval

        # --- Generate positions (only when cointegrated)
        positions = np.zeros(len(x))
        long_entry = (zscore < -entry_z) & coint_mask
        short_entry = (zscore > entry_z) & coint_mask
        exit_trade = (np.abs(zscore) < exit_z) | (~coint_mask)

        for i in range(1, len(x)):
            if long_entry[i]:
                positions[i] = 1
            elif short_entry[i]:
                positions[i] = -1
            elif exit_trade[i]:
                positions[i] = 0
            else:
                positions[i] = positions[i - 1]

                # --- Returns
        rx = pd.Series(x).pct_change().fillna(0)
        ry = pd.Series(y).pct_change().fillna(0)

        # Compute portfolio return using hedge ratio
        diff_y = ry.diff().fillna(0).values
        diff_x = rx.diff().fillna(0).values
        hedge = beta[:-1]

        port_ret = positions[:-1] * (diff_y - hedge * diff_x)  # type: ignore
        port_ret = pd.Series(port_ret).fillna(0)

        total_return = np.prod(1 + port_ret) - 1

        if np.std(port_ret) > 0:
            sharpe = np.mean(port_ret) / np.std(port_ret) * np.sqrt(252)
        else:
            sharpe = 0.0

        trades = int(np.sum(np.abs(np.diff(positions)) > 0))

        return {
            "total_return": round(float(total_return), 4),
            "sharpe": round(float(sharpe), 4),
            "trades": trades,
            "avg_beta": round(np.nanmean(beta), 4),
            "coint_valid_pct": round(np.nanmean(coint_mask) * 100, 2),
        }
