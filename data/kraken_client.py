import os
import time
from pathlib import Path

import pandas as pd
import requests

# --------------------------------------------------------------
# Configuration
# --------------------------------------------------------------
BASE_URL = "https://api.kraken.com/0/public/OHLC"
DATA_PATH = Path("data")
DATA_PATH.mkdir(exist_ok=True)

# Kraken OHLC intervals
INTERVAL_MAP = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}


# --------------------------------------------------------------
def download_ohlc(symbol: str, interval: str = "1m", since: int = None, max_batches: int = 100):
    """
    Downloads historical OHLCV data from Kraken’s public API.
    Kraken’s API allows about 720 data points per call (~12 hours for 1m interval).

    :param symbol: Kraken trading pair (e.g., BTC/USD)
    :param interval: One of ['1m','5m','15m','1h','4h','1d']
    :param since: Optional timestamp (in seconds)
    :param max_batches: Max requests to prevent overuse
    :return: DataFrame
    """
    kraken_symbol = symbol.replace("/", "")
    interval_value = INTERVAL_MAP.get(interval, 1)
    all_data = []

    print(f"📡 Downloading {symbol} @ {interval} from Kraken...")

    for i in range(max_batches):
        params = {"pair": kraken_symbol, "interval": interval_value}
        if since:
            params["since"] = since

        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "error" in data and data["error"]:
                print(f"⚠️ Kraken error: {data['error']}")
                break

            result = next(iter(data["result"].values()))
            if not result:
                print("⚠️ No more data returned.")
                break

            df = pd.DataFrame(
                result,
                columns=[
                    "time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "vwap",
                    "volume",
                    "count",
                ],
            )

            df["time"] = pd.to_datetime(df["time"], unit="s")
            all_data.append(df[["time", "open", "high", "low", "close", "volume"]])

            # Prepare for next batch
            since = int(df["time"].iloc[-1].timestamp())
            time.sleep(1.5)  # rate limit buffer

        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            time.sleep(5)
            continue

    if not all_data:
        print("❌ No data collected.")
        return pd.DataFrame()

    final_df = pd.concat(all_data, ignore_index=True).drop_duplicates(subset=["time"])
    final_df.sort_values("time", inplace=True)
    final_df.reset_index(drop=True, inplace=True)

    # Save to CSV
    filename = DATA_PATH / f"{symbol.replace('/', '_')}_{interval}.csv"
    final_df.to_csv(filename, index=False)
    print(f"✅ Saved {len(final_df)} rows → {filename}")

    return final_df


# --------------------------------------------------------------
def bulk_download(symbols=None, interval="1m"):
    """Download data for multiple symbols sequentially."""
    symbols = symbols or ["BTC/USD", "ETH/USD", "ADA/USD", "SOL/USD", "XRP/USD"]
    for sym in symbols:
        download_ohlc(sym, interval=interval)
        time.sleep(3)  # prevent rate limiting


# --------------------------------------------------------------
if __name__ == "__main__":
    print("⚙️ Kraken Historical Data Downloader")
    symbols = ["BTC/USD", "ETH/USD", "ADA/USD", "SOL/USD", "XRP/USD"]
    interval = "1m"  # can be "5m", "15m", etc.

    bulk_download(symbols, interval)
