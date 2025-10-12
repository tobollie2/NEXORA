# /tools/verify_strategies.py
"""
NEXORA Strategy Verification Utility
------------------------------------
Validates that all strategy modules exist, can be imported, and expose
their expected class interfaces.

Run:
    python tools/verify_strategies.py
"""

import importlib
import inspect
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))  # ensure root path is importable

STRATEGY_MODULES = {
    "strategies.trend_following": "TrendFollowingStrategy",
    "strategies.mean_reversion": "MeanReversionStrategy",
    "strategies.statistical_arbitrage": "StatisticalArbitrageStrategy",
}


def check_strategy_module(module_name: str, class_name: str):
    """
    Attempt to import a strategy module and verify it defines the required class.
    """
    print(f"🔍 Checking module: {module_name}")
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        print(f"❌ Module not found: {module_name}")
        return False

    if not hasattr(module, class_name):
        print(f"❌ Missing class: {class_name} in {module_name}")
        return False

    cls = getattr(module, class_name)
    if not inspect.isclass(cls):
        print(f"❌ {class_name} is not a valid class in {module_name}")
        return False

    instance = cls()
    required_methods = ["parameter_grid", "sample_parameters", "run_backtest"]
    missing_methods = [m for m in required_methods if not hasattr(instance, m)]

    if missing_methods:
        print(f"⚠️ Class {class_name} missing methods: {missing_methods}")
    else:
        print(f"✅ {class_name} validated successfully.")

    return True


def verify_all_strategies():
    print("🧠 Running NEXORA Strategy Verification...\n")
    passed = 0
    total = len(STRATEGY_MODULES)

    for module_name, class_name in STRATEGY_MODULES.items():
        if check_strategy_module(module_name, class_name):
            passed += 1

    print("\n📊 Summary:")
    print(f"   Passed: {passed}/{total}")
    if passed == total:
        print("   ✅ All strategies successfully verified.")
    else:
        print("   ❌ Some modules failed verification. Please fix before backtesting.")


if __name__ == "__main__":
    verify_all_strategies()
