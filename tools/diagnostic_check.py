"""
NEXORA Diagnostic Check Utility
-------------------------------
Verifies that the project structure, environment, and key dependencies
are correctly configured.
"""

import importlib
import os
import platform
import sys

import pandas as pd

# Define the root project directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Expected directories
EXPECTED_DIRS = [
    "core",
    "data",
    "strategies",
    "tools",
    "backtest",
    "monitoring",
    "portfolio",
    "logs",
]

# Key files that should exist
EXPECTED_FILES = ["main.py", "settings.yaml", "requirements.txt"]


# -------------------------------------------------------------------
def check_directories():
    print("\n📂 Checking directory structure:")
    for folder in EXPECTED_DIRS:
        path = os.path.join(ROOT_DIR, folder)
        if os.path.isdir(path):
            print(f"   ✅ Found directory: {folder}")
        else:
            print(f"   ⚠️ Missing directory: {folder}")


def check_files():
    print("\n📄 Checking important files:")
    for file in EXPECTED_FILES:
        path = os.path.join(ROOT_DIR, file)
        if os.path.exists(path):
            print(f"   ✅ Found file: {file}")
        else:
            print(f"   ⚠️ Missing file: {file}")


def check_imports():
    print("\n🧩 Verifying module imports:")
    modules = [
        "pandas",
        "numpy",
        "matplotlib",
        "plotly",
        "strategies.trend",
        "strategies.mean_reversion",
        "strategies.stat_arb",
        "backtest.backtest_runner",
        "tools.log_analyzer",
    ]
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"   ✅ Imported: {mod}")
        except Exception as e:
            print(f"   ❌ Failed: {mod} — {e}")


def check_data_files():
    data_dir = os.path.join(ROOT_DIR, "data", "cleaned")
    print("\n📊 Checking data files in:", data_dir)
    if not os.path.exists(data_dir):
        print("   ⚠️ No data directory found.")
        return

    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    if not csv_files:
        print("   ⚠️ No CSV files found.")
        return

    for f in csv_files:
        try:
            df = pd.read_csv(os.path.join(data_dir, f), nrows=5)
            print(f"   ✅ {f}: {len(df.columns)} columns — Sample OK")
        except Exception as e:
            print(f"   ❌ Error reading {f}: {e}")


def show_env_info():
    print("\n⚙️ Environment Info:")
    print(f"   Python: {sys.version}")
    print(f"   Platform: {platform.system()} {platform.release()}")
    print(f"   Interpreter: {sys.executable}")
    print(f"   Working Dir: {os.getcwd()}")


# -------------------------------------------------------------------
if __name__ == "__main__":
    print("\n🧠 Running NEXORA Diagnostic Check...\n")
    check_directories()
    check_files()
    check_imports()
    check_data_files()
    show_env_info()
    print("\n✅ Diagnostic check complete.\n")
