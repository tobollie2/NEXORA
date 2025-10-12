# backtest_runner.py
import os
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from backtest.performance_metrics import BacktestReportGenerator
from strategies.mean_reversion import MeanReversionStrategy
from strategies.statistical_arbitrage import StatisticalArbitrageStrategy
from strategies.trend_following import TrendFollowingStrategy


class BacktestRunner:
    """
    Runs all enabled strategies concurrently and aggregates results
    into CSV and HTML summaries for analysis.
    """

    def __init__(self):
        self.results_dir = os.path.join("F:", "NEXORA", "reports", "backtests")
        os.makedirs(self.results_dir, exist_ok=True)
        self.strategies = {
            "TrendFollowing": TrendFollowingStrategy,
            "MeanReversion": MeanReversionStrategy,
            "StatArbitrage": StatisticalArbitrageStrategy,
        }
        self.symbols = ["AAPL", "GOOG", "MSFT", "AMZN"]
        self.data_dir = os.path.join("F:", "NEXORA", "data", "cleaned")

    # -------------------------------------------------------------------------
    def run_strategy(self, strategy_cls, symbol: str) -> Dict[str, Any]:
        """
        Run a single strategy for a given symbol and return performance results.
        """
        try:
            strategy = strategy_cls()
            data_path = os.path.join(self.data_dir, f"{symbol}.csv")

            if not os.path.exists(data_path):
                raise FileNotFoundError(f"Missing data file: {data_path}")

            data = pd.read_csv(data_path)
            results = strategy.run(data)

            results["strategy"] = strategy_cls.__name__
            results["symbol"] = symbol
            print(f"✅ Completed {strategy_cls.__name__} on {symbol}")
            return results

        except Exception as e:
            print(f"❌ Error in {strategy_cls.__name__} on {symbol}: {e}")
            traceback.print_exc()
            return {
                "strategy": strategy_cls.__name__,
                "symbol": symbol,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    # -------------------------------------------------------------------------
    def run_all(self) -> List[Dict[str, Any]]:
        """
        Run all enabled strategies concurrently across all symbols.
        """
        print("\n🚀 Starting backtests for all strategies...\n")
        results = []
        futures = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            for strat_name, strat_cls in self.strategies.items():
                for symbol in self.symbols:
                    futures.append(executor.submit(self.run_strategy, strat_cls, symbol))

            for future in as_completed(futures):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    print(f"⚠️  Worker failed with: {e}")

        print(f"\n✅ Total completed strategy runs: {len(results)}")
        return results

    # -------------------------------------------------------------------------
    def save_summary(self, results: List[Dict[str, Any]]):
        """
        Save backtest results as CSV and generate HTML summary report.
        """
        if not results:
            print("\n⚠️ No results to save.")
            return

        df = pd.DataFrame(results)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_path = os.path.join(self.results_dir, f"backtest_summary_{timestamp}.csv")

        df.to_csv(csv_path, index=False)
        print(f"\n📊 Summary saved to: {csv_path}")

        try:
            report_dir = os.path.join("F:", "NEXORA", "reports", "backtests")
            report = BacktestReportGenerator(output_dir=report_dir)
            report.save_html_report(df, name=f"backtest_summary_{timestamp}.html")
            print("🧾 HTML report generated successfully.")
        except Exception as e:
            print(f"❌ Could not generate HTML report: {e}")
            traceback.print_exc()

    # -------------------------------------------------------------------------
    def run_pipeline(self):
        """Convenience wrapper: runs all tests and saves results."""
        results = self.run_all()
        self.save_summary(results)
        print("\n🎯 Backtesting pipeline completed successfully.\n")


# -------------------------------------------------------------------------
if __name__ == "__main__":
    runner = BacktestRunner()
    runner.run_pipeline()
