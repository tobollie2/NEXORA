import numpy as np


class RiskManager:
    """
    Advanced risk management for NEXORA.
    Tracks exposure, volatility, and dynamically adjusts risk limits.
    """

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.max_drawdown_limit = config.get("max_drawdown", 0.20)
        self.var_limit = config.get("var_limit", 0.05)
        self.vol_window = config.get("vol_window", 50)
        self.symbol_volatility = {}
        self.risk_state = "NORMAL"

    # -----------------------------------------------------------------
    def update_volatility(self, market_data):
        """Estimate rolling volatility per symbol using recent returns."""
        for symbol, data in market_data.items():
            prices = np.array(data["price_buffer"][-self.vol_window :])
            if len(prices) > 2:
                returns = np.diff(np.log(prices))
                vol = np.std(returns)
                self.symbol_volatility[symbol] = vol
        return self.symbol_volatility

    # -----------------------------------------------------------------
    def evaluate_risk(self, portfolio):
        """
        Evaluate overall portfolio risk state based on drawdown and exposure.
        """
        equity = getattr(portfolio, "current_equity", 1000)
        max_equity = getattr(portfolio, "peak_equity", equity)
        drawdown = (max_equity - equity) / max_equity if max_equity > 0 else 0

        exposure = getattr(portfolio, "total_exposure", 0)
        self.risk_state = "NORMAL"

        if drawdown > self.max_drawdown_limit:
            self.risk_state = "ALERT"
        if drawdown > (self.max_drawdown_limit * 1.5):
            self.risk_state = "CRITICAL"

        self.logger.info(
            f"⚖️ Risk Check | Equity: ${equity:,.2f} | DD: {drawdown*100:.2f}% | Exposure: {exposure:.2f} | State: {self.risk_state}"
        )

        return self.risk_state

    # -----------------------------------------------------------------
    def get_symbol_risk_limit(self, symbol):
        """Return per-symbol risk weight (lower for volatile assets)."""
        vol = self.symbol_volatility.get(symbol, 0.02)
        inv_vol = 1 / (vol + 1e-8)
        weight = inv_vol / np.sum(list(self.symbol_volatility.values()) or [1])
        return weight

    # -----------------------------------------------------------------
    def apply_stop_loss(self, portfolio):
        """Force liquidation if risk thresholds are breached."""
        if self.risk_state == "CRITICAL":
            self.logger.warning("🚨 CRITICAL drawdown detected — closing all positions.")
            portfolio.close_all()
