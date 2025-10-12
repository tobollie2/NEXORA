"""
optimization/optimizers/grid_search.py
-------------------------------------
Grid search optimizer for evaluating strategy parameter combinations.
Automatically detects and adapts to BacktestRunner API differences.
"""

from __future__ import annotations

import itertools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Local imports
from backtest.backtest_runner import BacktestRunner
from monitoring.logging_utils import setup_logger


class GridSearchOptimizer:
    """
    Exhaustive grid search optimizer for trading strategy parameters.
    Dynamically adapts to various BacktestRunner method signatures.
    """

    def __init__(self, strategy_name: str, param_grid: Dict[str, List[Any]], data_path: Path) -> None:
        self.strategy_name = strategy_name
        self.param_grid = param_grid
        self.data_path = data_path
        self.logger = setup_logger(f"GridSearchOptimizer[{strategy_name}]")

    def generate_param_combinations(self) -> List[Dict[str, Any]]:
        """Generate all parameter combinations from the provided grid."""
        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())
        combos = [dict(zip(keys, v)) for v in itertools.product(*values)]
        return combos

    def _get_runner_method(self, runner: BacktestRunner):
        """
        Dynamically detect which method the BacktestRunner supports.
        """
        possible_methods = ["run_backtest", "run", "execute", "start", "run_all"]
        for method_name in possible_methods:
            if hasattr(runner, method_name):
                self.logger.info(f"⚙️ Using BacktestRunner.{method_name}()")
                return getattr(runner, method_name)
        raise AttributeError(
            "❌ BacktestRunner has no supported execution method. Expected one of: "
            + ", ".join(possible_methods)
        )

    def run(self) -> None:
        """Run the grid search across all parameter combinations."""
        all_params = self.generate_param_combinations()
        total = len(all_params)

        self.logger.info(f"🚀 Starting grid search for strategy '{self.strategy_name}'")
        self.logger.info(f"🔍 Total parameter combinations: {total}")

        results: List[Dict[str, Any]] = []

        for i, params in enumerate(all_params, start=1):
            self.logger.info(f"Running backtest {i}/{total} with params: {params}")
            try:
                runner = BacktestRunner()
                run_fn = self._get_runner_method(runner)

                # Attempt flexible argument matching
                try:
                    metrics = run_fn(
                        data_path=self.data_path,
                        params=params,
                        strategy_name=self.strategy_name,
                    )
                except TypeError:
                    try:
                        metrics = run_fn(data_path=self.data_path, params=params)
                    except TypeError:
                        metrics = run_fn()

                fitness = 0.0
                if isinstance(metrics, dict):
                    fitness = float(metrics.get("fitness", 0.0))

                results.append({"params": params, "fitness": fitness})
                self.logger.info(f"✅ Completed {i}/{total} | Fitness={fitness:.4f}")

            except Exception as e:
                self.logger.error(f"❌ Failed run {i}/{total}: {e}")
                continue

        if not results:
            self.logger.warning("⚠️ No valid results found in grid search.")
            return

        # Sort results by descending fitness
        results.sort(key=lambda x: x["fitness"], reverse=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = Path("logs/optimization_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"grid_results_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        best = results[0]
        self.logger.info(f"🏆 Best configuration: {best['params']} | Fitness={best['fitness']:.4f}")
        self.logger.info(f"📊 Saved sorted results → {output_file}")
        self.logger.info("✅ Grid search complete.")


if __name__ == "__main__":
    print("🔧 Running GridSearchOptimizer self-test...")

    param_grid = {
        "window": [10, 20],
        "threshold": [0.1, 0.2],
    }

    grid_search = GridSearchOptimizer(
        strategy_name="statistical_arbitrage",
        param_grid=param_grid,
        data_path=Path("data/cleaned/BTC_USD_1m_cleaned.csv"),
    )

    grid_search.run()
