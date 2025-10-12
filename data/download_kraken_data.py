import os
import time
import requests
import pandas as pd
from pathlib import Path

# ================================================================
# 🔹 NEXORA Kraken Historical Data Downloader
# ================================================================

BASE_URL = "https://api.kraken.com/0/public/OHLC"
DATA_PATH = Path("data")
DATA_PATH.mkdir(exist_ok=True)

# Kraken uses specific ticker codes (e.g., BTC → XBT, DOGE → XDG)
SYMBOL_MAP = {
    "BTC/USD": "XBTUSD",
    "ETH/USD": "ETHUSD",
    "ADA/USD": "ADAUSD",
    "SOL/USD": "SOLUSD",
    "XRP/USD": "XRPUSD",
    "DOGE/USD": "XDGUSD",
    "LTC/USD": "LTCUSD",
    "DOT/USD": "DOTUSD",
    "BNB/USD": "BNBUSD",
    "LINK/USD": "LINKUSD",
    "MATIC/USD": "MATICUSD",
}

INTERVAL_MAP = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}


# ================================================================
def get_last_timestamp(csv_path: Path) -> int | None:
    """If a CSV already exists, return the last timestamp to resume from."""
    if csv_path.exists() and csv_path.stat().st_size > 0:
        try:
            df = pd.read_csv(csv_path)
            if "time" in df.columns and len(df) > 0:
                last_time = pd.to_datetime(df["time"].iloc[-1])
                return int(last_time.timestamp())
        except Exception:
            pass
    return None


# ================================================================
def download_full_history(symbol: str, interval: str = "1m", save_every: int = 10):
    """
    Download full historical OHLCV data from Kraken for a given symbol/interval.
    Automatically resumes from the last saved timestamp.
    """
    kraken_symbol = SYMBOL_MAP.get(symbol, symbol.replace("/", ""))
    interval_value = INTERVAL_MAP.get(interval, 1)
    filename = DATA_PATH / f"{symbol.replace('/', '_')}_{interval}_full.csv"

    since = get_last_timestamp(filename)
    all_data = []
    batch = 0

    if since:
        print(f"\n🔁 Resuming {symbol} from {pd.to_datetime(since, unit='s')}")
    else:
        print(
            f"\n📡 Starting full history download for {symbol} ({kraken_symbol}) @ {interval}"
        )

    while True:
        params = {"pair": kraken_symbol, "interval": interval_value}
        if since:
            params["since"] = since

        try:
            response = requests.get(BASE_URL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()

            if data.get("error"):
                print(f"⚠️ Kraken API error: {data['error']}")
                time.sleep(10)
                continue

            result = list(data["result"].values())[0]
            if not result:
                print("✅ No more data available — full history complete.")
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
            df[["open", "high", "low", "close", "vwap", "volume"]] = df[
                ["open", "high", "low", "close", "vwap", "volume"]
            ].astype(float)

            all_data.append(df[["time", "open", "high", "low", "close", "volume"]])
            since = int(df["time"].iloc[-1].timestamp())
            batch += 1

            print(f"📦 Batch {batch}: {len(df)} rows → latest {df['time'].iloc[-1]}")

            # Save progress every few batches
            if batch % save_every == 0:
                combined_df = pd.concat(all_data, ignore_index=True)
                if filename.exists():
                    old_df = pd.read_csv(filename)
                    combined_df = pd.concat([old_df, combined_df]).drop_duplicates(
                        subset=["time"]
                    )
                combined_df.to_csv(filename, index=False)
                print(f"💾 Progress saved ({len(combined_df)} total rows).")

            time.sleep(1.5)  # Rate-limit buffer

        except requests.exceptions.RequestException as e:
            print(f"🌐 Network issue: {e} — retrying in 15s...")
            time.sleep(15)
            continue
        except Exception as e:
            print(f"🚨 Unexpected error: {e}")
            break

    if all_data:
        new_df = pd.concat(all_data, ignore_index=True)
        if filename.exists():
            existing = pd.read_csv(filename)
            new_df = pd.concat([existing, new_df]).drop_duplicates(subset=["time"])
        new_df.sort_values("time", inplace=True)
        new_df.reset_index(drop=True, inplace=True)
        new_df.to_csv(filename, index=False)
        print(f"✅ Final dataset saved → {filename} ({len(new_df)} rows total)")
    else:
        print(f"⚠️ No new data collected for {symbol}.")


# ================================================================
def bulk_download(symbols=None, interval="1m"):
    """Sequentially download or resume full history for multiple symbols."""
    symbols = symbols or list(SYMBOL_MAP.keys())
    print("\n⚙️ Starting Kraken full historical data download...\n")

    for sym in symbols:
        try:
            download_full_history(sym, interval=interval)
        except Exception as e:
            print(f"❌ Failed for {sym}: {e}")
        time.sleep(2)

    print("\n🏁 All downloads completed successfully.")


# ================================================================
if __name__ == "__main__":
    # --- Select intervals and symbols here ---
    symbols_to_download = [
        "BTC/USD",
        "ETH/USD",
        "ADA/USD",
        "SOL/USD",
        "XRP/USD",
        "DOGE/USD",
        "LTC/USD",
        "DOT/USD",
        "BNB/USD",
        "LINK/USD",
        "MATIC/USD",
    ]

    # Recommended: "5m" or "1h" for large backtests
    bulk_download(symbols_to_download, interval="5m")
