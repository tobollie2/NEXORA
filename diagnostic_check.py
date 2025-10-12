"""
NEXORA Diagnostic Tool
----------------------
Checks environment, modules, file integrity, and strategy readiness.
"""

import importlib
import os
import sys
from pathlib import Path

log_path = Path("logs/system_health.json")
print(log_path.name)


import pandas as pd

print("🔍 Running NEXORA Diagnostic Check...\n")

# ---------------------------------------------------------------------
# 1️⃣  Verify Project Structure
# ---------------------------------------------------------------------
expected_dirs = [
    "config",
    "data",
    "logs",
    "strategies",
    "portfolio",
    "risk",
    "monitoring",
    "backtest",
]

print("📁 Checking directory structure:")
for d in expected_dirs:
    if not os.path.exists(d):
        print(f"❌ Missing directory: {d}")
    else:
        print(f"✅ Found directory: {d}")
print()

# ---------------------------------------------------------------------
# 2️⃣  Verify Key Files Exist
# ---------------------------------------------------------------------
expected_files = [
    "config/settings.yaml",
    "portfolio/allocator.py",
    "risk/risk_manager.py",
    "monitoring/logging_utils.py",
    "backtest/backtest_runner.py",
    "backtest/report_generator.py",
    "strategies/trend.py",
    "strategies/mean_reversion.py",
    "strategies/stat_arb.py",
]

print("📜 Checking critical files:")
for f in expected_files:
    if not os.path.exists(f):
        print(f"❌ Missing file: {f}")
    else:
        print(f"✅ Found file: {f}")
print()

# ---------------------------------------------------------------------
# 3️⃣  Test Imports
# ---------------------------------------------------------------------
modules_to_test = [
    "config.settings_loader",
    "portfolio.allocator",
    "risk.risk_manager",
    "monitoring.logging_utils",
    "strategies.trend",
    "strategies.mean_reversion",
    "strategies.stat_arb",
    "backtest.report_generator",
]

print("🧠 Testing imports:")
for mod in modules_to_test:
    try:
        importlib.import_module(mod)
        print(f"✅ Import OK → {mod}")
    except Exception as e:
        print(f"❌ Import FAILED → {mod}: {e}")
print()

# ---------------------------------------------------------------------
# 4️⃣  Validate Data Files
# ---------------------------------------------------------------------
data_dir = Path("data/cleaned")
if data_dir.exists():
    files = list(data_dir.glob("*.csv"))
    if not files:
        print("⚠️ No cleaned CSV data files found in data/cleaned/")
    else:
        print(f"📊 Found {len(files)} data files:")
        for f in files[:5]:
            try:
                df = pd.read_csv(f, nrows=3)
                cols = list(df.columns)
                print(f"   ✅ {f.name} → Columns: {cols}")
            except Exception as e:
                print(f"   ❌ Error reading {f.name}: {e}")
else:
    print("❌ data/cleaned/ directory missing.")
print()

# ---------------------------------------------------------------------
# 5️⃣  Confirm Python Environment
# ---------------------------------------------------------------------
print("🐍 Python environment:")
print(f"   Python: {sys.version}")
print(f"   Path: {sys.executable}")
print("\n✅ Diagnostic check complete.\n")
