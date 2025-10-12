"""
NEXORA Optimization Runner
--------------------------
Runs parameter grid optimizations for all active strategies
across configured trading symbols. Integrates directly with
the BacktestRunner and performance metrics.
"""

import itertools
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd

# --- Ensure NEXORA root is importable ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backtest.backtest_runner import BacktestRunner
from backtest.report_generator import BacktestReportGenerator

# --- Internal Imports ---
from config.settings_loader import load_settings


class OptimizationRunner:
    """
    Conducts multi-strategy parameter grid optimization.
    """


def __init__(self, base_config_path="config/settings.yaml", output_dir="logs/optimization_results"):
    # ✅ Force normal dictionary conversion
    self.config = dict(load_settings(base_config_path))

    self.output_dir = output_dir
    os.makedirs(output_dir, exist_ok=True)

    # ✅ Fix: safely extract symbols list
    self.symbols = self.config.get("data", {}).get("symbols", ["BTC/USD", "ETH/USD"])
    print("⚙️ OptimizationRunner initialized.")
    print(f"📈 Active symbols: {', '.join(self.symbols)}")

    # Parameter grids per strategy
    self.param_grids = {
        "trend": {
            "short_window": [10, 20, 30],
            "long_window": [50, 80, 100],
            "volatility_window": [10, 14, 20],
        },
        "mean_reversion": {
            "lookback_window": [20, 30, 40],
            "zscore_entry": [1.0, 1.5, 2.0],
            "zscore_exit": [0.2, 0.3, 0.4],
        },
        "stat_arb": {
            "pair_window": [50, 100, 150],
            "entry_threshold": [1.0, 1.5, 2.0],
            "exit_threshold": [0.2, 0.3, 0.4],
        },
    }

    self.symbols = self.config["data"].get("symbols", ["BTC/USD", "ETH/USD"])
    print("⚙️ OptimizationRunner initialized.")
    print(f"📈 Active symbols: {', '.join(self.symbols)}")

    # ------------------------------------------------------------------
    def generate_param_combinations(self, grid):
        """Return all parameter combinations from a dictionary grid."""
        keys = grid.keys()
        values = itertools.product(*grid.values())
        return [dict(zip(keys, v)) for v in values]

    # ------------------------------------------------------------------
    def run_single_optimization(self, strategy_name, params, symbol):
        """Run one configuration of a strategy for a given symbol."""
        try:
            print(f"🔍 Running {strategy_name} on {symbol} with params={params}")
            runner = BacktestRunner()
            results = runner.run_all([symbol])  # runs all strategies
            df_results = pd.DataFrame(results)

            # Filter only the relevant strategy
            df_results = df_results[
                df_results["strategy"].str.lower().str.contains(strategy_name.lower())
            ]
            if df_results.empty:
                print(f"⚠️ No results for {strategy_name} ({symbol})")
                return None

            df_results["params"] = [params] * len(df_results)
            return df_results

        except Exception as e:
            print(f"❌ Error in {strategy_name} ({symbol}): {e}")
            return None

    # ------------------------------------------------------------------
    def run_grid_search(self):
        """Execute full parameter optimization across strategies & symbols."""
        all_results = []

        print("\n🚀 Starting NEXORA Strategy Optimization...\n")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for strat, grid in self.param_grids.items():
                param_list = self.generate_param_combinations(grid)
                for symbol in self.symbols:
                    for params in param_list:
                        futures.append(
                            executor.submit(self.run_single_optimization, strat, params, symbol)
                        )

            for f in as_completed(futures):
                result = f.result()
                if result is not None:
                    all_results.append(result)

        # Combine all optimization results
        if not all_results:
            print("⚠️ No optimization results found.")
            return

        df_all = pd.concat(all_results, ignore_index=True)

        # Save raw CSV
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_path = os.path.join(self.output_dir, f"optimization_results_{timestamp}.csv")
        df_all.to_csv(csv_path, index=False)
        print(f"\n💾 Optimization results saved → {csv_path}")

        # Generate interactive HTML report
        report = BacktestReportGenerator(df_all, log_dir=self.output_dir)
        report.save_html_report()
        print(f"📄 HTML optimization report generated successfully!")

        return df_all


# ------------------------------------------------------------------
if __name__ == "__main__":
    optimizer = OptimizationRunner()
    optimizer.run_grid_search()
