import asyncio
import os
import random
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


class DataIngestion:
    """
    Multi-mode market data ingestion engine for NEXORA.
    Supports: SIMULATED, HISTORICAL (CSV), and WEBSOCKET (future).
    """

    def __init__(
        self,
        mode="SIMULATED",
        symbols=None,
        buffer_size=500,
        logger=None,
        data_path="data/",
    ):
        self.mode = mode.upper()
        self.symbols = symbols or ["BTC/USD"]
        self.buffer_size = buffer_size
        self.logger = logger
        self.data_path = Path(data_path)
        self.buffers = {symbol: [] for symbol in self.symbols}
        self.pointer = {symbol: 0 for symbol in self.symbols}  # For historical replay

        # Data holders for HISTORICAL mode
        self.historical_data = {}

        # --- Mode-specific initialization ---
        if self.mode == "HISTORICAL":
            self._load_historical_data()
        elif self.mode == "SIMULATED":
            self.logger.info("📈 Using simulated random-walk data.")
        elif self.mode == "WEBSOCKET":
            self.logger.warning("🌐 WebSocket mode initialized (not yet active).")
        else:
            raise ValueError(f"❌ Unknown data mode: {self.mode}")

    # --------------------------------------------------------------------------
    # HISTORICAL MODE
    # --------------------------------------------------------------------------
    def _load_historical_data(self):
        """
        Load CSVs for each symbol and prepare for sequential replay.
        Expects files like: data/BTC_USD_1m.csv
        """
        for symbol in self.symbols:
            clean_name = symbol.replace("/", "_")
            file_path = self.data_path / f"{clean_name}_1m.csv"

            if not file_path.exists():
                self.logger.error(f"❌ Missing CSV for {symbol}: {file_path}")
                continue

            df = pd.read_csv(file_path)
            df.columns = [c.lower() for c in df.columns]
            expected_cols = {"time", "open", "high", "low", "close", "volume"}
            if not expected_cols.issubset(df.columns):
                raise ValueError(f"❌ {file_path} missing required OHLCV columns.")

            df["time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")
            df.dropna(subset=["time"], inplace=True)
            df.sort_values("time", inplace=True)
            df.reset_index(drop=True, inplace=True)

            self.historical_data[symbol] = df
            self.logger.info(f"📊 Loaded {len(df)} rows for {symbol} from {file_path}")

    # --------------------------------------------------------------------------
    async def get_latest_data(self):
        """
        Async method returning the most recent candle data for each symbol.
        In HISTORICAL mode, replays candles sequentially.
        In SIMULATED mode, generates synthetic candles.
        """
        data_snapshot = {}

        for symbol in self.symbols:
            if self.mode == "HISTORICAL":
                df = self.historical_data.get(symbol)
                idx = self.pointer[symbol]

                if df is None or idx >= len(df):
                    self.logger.warning(f"⏹️ End of historical data for {symbol}")
                    continue

                row = df.iloc[idx]
                data = {
                    "symbol": symbol,
                    "time": row["time"],
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["volume"],
                }

                # Advance pointer
                self.pointer[symbol] += 1

            elif self.mode == "SIMULATED":
                # Simulate a price candle
                last_price = (
                    self.buffers[symbol][-1]["close"]
                    if self.buffers[symbol]
                    else random.uniform(20000, 30000)
                )
                change = random.uniform(-0.003, 0.003)
                open_price = last_price
                close_price = last_price * (1 + change)
                high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.001))
                low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.001))
                volume = random.uniform(0.5, 5.0)

                data = {
                    "symbol": symbol,
                    "time": datetime.utcnow(),
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                }

            else:
                # WebSocket placeholder (to be added later)
                data = {"symbol": symbol, "time": datetime.utcnow(), "close": np.nan}

            # Maintain rolling buffer
            self.buffers[symbol].append(data)
            if len(self.buffers[symbol]) > self.buffer_size:
                self.buffers[symbol].pop(0)

            data_snapshot[symbol] = data

        await asyncio.sleep(0)  # Yield control
        return data_snapshot

    # --------------------------------------------------------------------------
    def get_buffer_dataframe(self, symbol):
        """Return recent data as DataFrame."""
        if symbol not in self.buffers:
            return pd.DataFrame()
        return pd.DataFrame(self.buffers[symbol])
