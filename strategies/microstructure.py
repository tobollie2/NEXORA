import numpy as np


class MicrostructureFilter:
    """Execution filter: validates signals with order book imbalance + VWAP."""

    def __init__(self, logger=None, config=None):
        self.logger = logger
        self.config = config
        self.obi_threshold = 0.3  # minimum imbalance to confirm

    def _calc_vwap(self, trades):
        """Calculate VWAP from recent trades."""
        if not trades:
            return None
        prices = np.array([t["price"] for t in trades])
        sizes = np.array([t["size"] for t in trades])
        return np.sum(prices * sizes) / np.sum(sizes)

    def _calc_obi(self, order_book):
        """Order Book Imbalance (OBI): (bid_vol - ask_vol) / (bid_vol + ask_vol)."""
        bid_vol = sum([b[1] for b in order_book["bids"]])
        ask_vol = sum([a[1] for a in order_book["asks"]])
        if bid_vol + ask_vol == 0:
            return 0
        return (bid_vol - ask_vol) / (bid_vol + ask_vol)

    def confirm(self, signal, market_data):
        """
        Confirm or reject a signal using market microstructure.
        - Long needs buy imbalance (OBI > 0.3) and price < VWAP.
        - Short needs sell imbalance (OBI < -0.3) and price > VWAP.
        """
        pair = signal["pair"]
        if pair not in market_data:
            return False

        md = market_data[pair]
        vwap = self._calc_vwap(md["trades"])
        obi = self._calc_obi(md["order_book"])
        price = signal.get("price", md["ohlcv"]["close"])

        confirmed = False
        if signal["direction"] == "LONG":
            confirmed = obi > self.obi_threshold and (vwap is None or price < vwap)
        elif signal["direction"] == "SHORT":
            confirmed = obi < -self.obi_threshold and (vwap is None or price > vwap)

        if confirmed:
            if self.logger:
                self.logger.info(f"Microstructure confirmed signal: {signal}")
        else:
            if self.logger:
                self.logger.info(f"Microstructure rejected signal: {signal}")

        return confirmed
