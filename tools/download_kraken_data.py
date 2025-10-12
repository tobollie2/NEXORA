import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# ================================================================
# 🔹 Kraken Historical Data Downloader (Full History, Auto-Resume)
# ================================================================

DATA_PATH = Path("data/kraken")
DATA_PATH.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.kraken.com/0/public/OHLC"

# Pairs and intervals to fetch
SYMBOLS = [
    "BTC/USD",
    "ETH/USD",
    "SOL/USD",
    "XRP/USD",
    "ADA/USD",
    "DOT/USD",
    "LTC/USD",
    "BNB/USD",
    "LINK/USD",
]
INTERVALS = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}

# Kraken API rate limit guideline: ~1 request/sec
API_DELAY = 1.2


# ================================================================
def fetch_kraken_ohlcv(pair: str, interval: int, since=None):
    """Fetch OHLC data from Kraken API."""
    params = {"pair": pair.replace("/", ""), "interval": interval}
    if since:
        params["since"] = since
    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if "error" in data and data["error"]:
            print(f"⚠️ API error for {pair}: {data['error']}")
            return None
        key = list(data["result"].keys())[0]
        return data["result"][key]
    except Exception as e:
        print(f"❌ Error fetching {pair} ({interval}m): {e}")
        return None


# ================================================================
def save_to_csv(pair: str, interval_str: str, new_data):
    """Append new OHLC data to an existing CSV, avoiding duplicates."""
    filename = DATA_PATH / f"{pair.replace('/', '_')}_{interval_str}_full.csv"

    df_new = pd.DataFrame(
        new_data,
        columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"],
    )
    df_new["time"] = pd.to_datetime(df_new["time"], unit="s")
    df_new = df_new.drop_duplicates(subset=["time"]).sort_values("time")

    if filename.exists():
        df_old = pd.read_csv(filename)
        df_old["time"] = pd.to_datetime(df_old["time"])
        df = pd.concat([df_old, df_new], ignore_index=True).drop_duplicates(subset=["time"])
        print(f"📈 Appended {len(df_new)} new rows → {filename.name}")
    else:
        df = df_new
        print(f"🆕 Created new file for {pair} ({interval_str})")

    df.to_csv(filename, index=False)


# ================================================================
def download_all():
    """Fetch all data for all pairs and intervals."""
    print("\n🚀 Starting Kraken Historical Data Downloader...\n")

    for pair in SYMBOLS:
        for interval_str, interval in INTERVALS.items():
            print(f"⏳ Fetching {pair} ({interval_str})...")

            last_timestamp = None
            filename = DATA_PATH / f"{pair.replace('/', '_')}_{interval_str}_full.csv"

            # Resume from last timestamp if file exists
            if filename.exists():
                df_existing = pd.read_csv(filename)
                if not df_existing.empty:
                    last_timestamp = int(pd.to_datetime(df_existing["time"].iloc[-1]).timestamp())
                    print(f"🔁 Resuming from {datetime.utcfromtimestamp(last_timestamp)}")

            # Fetch paginated historical data
            while True:
                ohlcv = fetch_kraken_ohlcv(pair, interval, since=last_timestamp)
                if not ohlcv:
                    print(f"⚠️ No more data or API limit reached for {pair} ({interval_str}).")
                    break

                save_to_csv(pair, interval_str, ohlcv)
                last_timestamp = int(ohlcv[-1][0])
                time.sleep(API_DELAY)

            print(f"✅ Completed {pair} ({interval_str})\n")

    print("\n🎯 All historical data downloaded successfully!")


# ================================================================
if __name__ == "__main__":
    download_all()
