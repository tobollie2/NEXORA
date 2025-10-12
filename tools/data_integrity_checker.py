import pandas as pd
from pathlib import Path

# ================================================================
# 🔹 UNIVERSAL NEXORA DATA INTEGRITY & AUTO-FIX TOOL
# ================================================================

# Automatically detects CSVs from any subfolder under /data/
DATA_PATH = Path("data")

# Interval map (used to determine expected frequency)
INTERVAL_MAP = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "1h": "1H",
    "4h": "4H",
    "1d": "1D",
}


# ================================================================
def detect_interval_from_filename(filename: str) -> str:
    """Extract interval (e.g. '5m') from filename."""
    for key in INTERVAL_MAP:
        if (
            f"_{key}_" in filename
            or filename.endswith(f"_{key}.csv")
            or filename.endswith(f"_{key}_full.csv")
        ):
            return key
    return "1m"  # default


# ================================================================
def merge_partials(base_file: Path):
    """Merge _partial.csv files for the same symbol automatically."""
    symbol_prefix = base_file.stem.replace("_full", "").split("_")[0]
    partials = list(base_file.parent.glob(f"{symbol_prefix}_*_partial*.csv"))

    if not partials:
        return None

    print(f"🔄 Found {len(partials)} partial files for {symbol_prefix}, merging...")

    merged_data = []
    for p in partials:
        try:
            df = pd.read_csv(p)
            merged_data.append(df)
        except Exception as e:
            print(f"⚠️ Skipping corrupted file {p.name}: {e}")

    if not merged_data:
        print("⚠️ No valid partial files to merge.")
        return None

    df_combined = pd.concat(merged_data, ignore_index=True)
    print(f"🧩 Merged {len(merged_data)} partials into memory for {symbol_prefix}.")
    return df_combined


# ================================================================
def fix_and_validate(file_path: Path, fill_gaps=True):
    """Validates, merges, and cleans a single Kraken dataset."""
    print(f"\n🔍 Checking {file_path.relative_to(DATA_PATH)}")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return None

    # Detect interval
    interval_str = detect_interval_from_filename(file_path.name)
    expected_freq = INTERVAL_MAP[interval_str]

    # --- Merge partials (if any) ---
    partial_data = merge_partials(file_path)
    if partial_data is not None:
        df = pd.concat([df, partial_data], ignore_index=True)

    # --- Basic validation ---
    if "time" not in df.columns:
        print("❌ Missing 'time' column — skipping file.")
        return None

    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time").drop_duplicates(subset=["time"])
    df = df.reset_index(drop=True)

    # --- Check time continuity ---
    start, end = df["time"].iloc[0], df["time"].iloc[-1]
    expected_range = pd.date_range(start=start, end=end, freq=expected_freq)
    missing = len(expected_range) - len(df)

    print(f"🕒 Range: {start.date()} → {end.date()} | Interval: {interval_str}")
    print(f"📊 Candles: {len(df):,} | Missing: {missing:,}")

    # --- Fill small gaps (<1%) ---
    if fill_gaps and 0 < missing / len(expected_range) < 0.01:
        print("🧱 Small gaps detected — forward-filling missing intervals.")
        df = df.set_index("time").reindex(expected_range)
        df = df.ffill().reset_index().rename(columns={"index": "time"})

    # --- Save cleaned data ---
    cleaned_dir = file_path.parent / "cleaned"
    cleaned_dir.mkdir(exist_ok=True)
    cleaned_path = cleaned_dir / f"{file_path.stem}_cleaned.csv"
    df.to_csv(cleaned_path, index=False)
    print(f"✅ Cleaned dataset exported → {cleaned_path.relative_to(DATA_PATH)}")

    return {
        "file": str(file_path.relative_to(DATA_PATH)),
        "interval": interval_str,
        "rows": len(df),
        "missing": missing,
        "coverage": round(100 - (missing / max(len(df), 1) * 100), 2),
    }


# ================================================================
def run_integrity_check():
    """Scans all Kraken CSVs recursively and validates them."""
    print("\n🧩 Starting NEXORA Universal Data Integrity + Auto-Fix Check...\n")

    # Recursively search all subdirectories
    csv_files = list(DATA_PATH.rglob("*.csv"))
    if not csv_files:
        print("⚠️ No Kraken CSV files found anywhere under /data/.")
        return

    print(f"📂 Found {len(csv_files)} CSV files for validation.\n")

    summary = []
    for f in csv_files:
        result = fix_and_validate(f, fill_gaps=True)
        if result:
            summary.append(result)

    # --- Summary report ---
    if summary:
        df_summary = pd.DataFrame(summary)
        report_path = DATA_PATH / "integrity_universal_report.csv"
        df_summary.to_csv(report_path, index=False)
        print("\n📘 INTEGRITY SUMMARY")
        print(df_summary.to_string(index=False))
        print(f"\n🧾 Report saved → {report_path}")


# ================================================================
if __name__ == "__main__":
    run_integrity_check()
