"""
optimization/optimization_runner.py
-----------------------------------
NEXORA Parallel Optimization Framework

Now supports:
- Grid Search (parallelized)
- Genetic Algorithm (parallelized fitness evaluation)
- Bayesian Optimization (Optuna-driven, with built-in concurrency)

Designed for large-scale trading strategy optimization across CPUs/GPUs.
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Callable

from monitoring.logging_utils import setup_logger

# Core optimizers
from optimization.optimizers.grid_search import GridSearchOptimizer
from optimization.optimizers.genetic_opt import GeneticOptimizer

# Optional Bayesian backend
try:
    import optuna
    from optuna import Trial
except ImportError:
    optuna = None


class OptimizationRunner:
    """
    Central orchestrator for all NEXORA optimization modes,
    including parallelized execution for grid/genetic algorithms.
    """

    def __init__(
        self,
        strategy_name: str,
        mode: str,
        data_path: Path,
        param_config: Dict[str, Any],
        output_dir: Path | None = None,
        max_workers: int | None = None,
    ) -> None:
        self.strategy_name = strategy_name
        self.mode = mode.lower()
        self.data_path = data_path
        self.param_config = param_config
        self.output_dir = output_dir or Path("logs/optimization_results")
        self.logger = setup_logger(f"OptimizationRunner[{strategy_name}]")

        self.max_workers = max_workers or max(os.cpu_count() - 1, 1)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"📂 Output directory set to: {self.output_dir}")
        self.logger.info(f"⚙️ Using up to {self.max_workers} parallel workers")

    # ----------------------------------------------------------------------
    # Factory Method
    # ----------------------------------------------------------------------
    def get_optimizer(self):
        """Return the appropriate optimizer object or callable."""
        if self.mode == "grid":
            self.logger.info("🧮 Using Parallel Grid Search Optimization")
            return self._run_parallel_grid_search

        elif self.mode == "genetic":
            self.logger.info("🧬 Using Parallel Genetic Optimization")
            return self._run_parallel_genetic_optimization

        elif self.mode == "bayesian":
            if optuna is None:
                raise ImportError(
                    "❌ Bayesian optimization requires `optuna`. Install it with: pip install optuna"
                )
            self.logger.info("🧠 Using Bayesian Optimization (Optuna backend)")
            return self._run_bayesian_optimization

        else:
            raise ValueError(f"❌ Unsupported optimization mode: '{self.mode}'")

    # ----------------------------------------------------------------------
    # Entry point
    # ----------------------------------------------------------------------
    def run(self) -> None:
        """Execute the selected optimizer and handle results."""
        self.logger.info(f"🚀 Starting optimization ({self.mode}) for {self.strategy_name}")
        optimizer_fn = self.get_optimizer()

        try:
            optimizer_fn()
        except Exception as e:
            self.logger.error(f"❌ Optimization failed: {e}")
            raise

        summary_path = self._save_summary()
        self.logger.info(f"✅ Optimization summary saved → {summary_path}")

    # ----------------------------------------------------------------------
    # Parallel Grid Search
    # ----------------------------------------------------------------------
    def _run_parallel_grid_search(self) -> None:
        """Execute grid search using multiple cores."""
        from backtest.backtest_runner import BacktestRunner
        import itertools

        runner = BacktestRunner()
        run_fn = self._detect_runner_method(runner)

        param_keys = list(self.param_config.keys())
        param_values = list(itertools.product(*self.param_config.values()))
        total_combinations = len(param_values)

        self.logger.info(f"🔍 Running {total_combinations} parameter combinations in parallel...")

        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._safe_run, run_fn, dict(zip(param_keys, combo))): combo
                for combo in param_values
            }

            for future in as_completed(futures):
                params = futures[future]
                try:
                    res = future.result()
                    if res:
                        results.append(res)
                        self.logger.info(f"✅ Completed {params}")
                except Exception as e:
                    self.logger.error(f"❌ Failed {params}: {e}")

        self._save_results(results, "grid_parallel")

    # ----------------------------------------------------------------------
    # Parallel Genetic Optimization
    # ----------------------------------------------------------------------
    def _run_parallel_genetic_optimization(self) -> None:
        """Execute genetic optimization with parallel fitness evaluation."""
        from backtest.backtest_runner import BacktestRunner
        import random

        param_bounds = self.param_config
        population_size = 10
        generations = 4

        self.logger.info(f"🧬 Genetic optimization with {population_size}x{generations} evaluations")

        def random_individual():
            return {
                key: random.uniform(bounds[0], bounds[1])
                if isinstance(bounds[0], (int, float))
                else random.choice(bounds)
                for key, bounds in param_bounds.items()
            }

        def evaluate_population(population):
            """Evaluate all individuals in parallel."""
            results = []
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._safe_run, run_fn, individual): individual
                    for individual in population
                }
                for future in as_completed(futures):
                    individual = futures[future]
                    try:
                        res = future.result()
                        if res:
                            results.append((individual, res))
                    except Exception as e:
                        self.logger.error(f"❌ Failed individual {individual}: {e}")
            return results

        runner = BacktestRunner()
        run_fn = self._detect_runner_method(runner)

        population = [random_individual() for _ in range(population_size)]
        all_results = []

        for gen in range(generations):
            self.logger.info(f"🧬 Generation {gen + 1}/{generations}")
            evaluated = evaluate_population(population)
            evaluated.sort(key=lambda x: x[1].get("fitness", 0), reverse=True)
            all_results.extend(evaluated)

            # Select top performers for crossover
            top_individuals = [ind for ind, _ in evaluated[: population_size // 2]]
            next_gen = []
            for _ in range(population_size):
                p1, p2 = random.sample(top_individuals, 2)
                child = {
                    key: random.choice([p1[key], p2[key]]) for key in param_bounds.keys()
                }
                if random.random() < 0.15:
                    mut_key = random.choice(list(param_bounds.keys()))
                    bounds = param_bounds[mut_key]
                    child[mut_key] = (
                        random.uniform(bounds[0], bounds[1])
                        if isinstance(bounds[0], (int, float))
                        else random.choice(bounds)
                    )
                next_gen.append(child)
            population = next_gen

        self._save_results([r for _, r in all_results], "genetic_parallel")

    # ----------------------------------------------------------------------
    # Bayesian Optimization (unchanged)
    # ----------------------------------------------------------------------
    def _run_bayesian_optimization(self) -> None:
        """Perform Bayesian optimization using Optuna."""
        import optuna

        self.logger.info(f"🧠 Starting Bayesian Optimization for {self.strategy_name}")

        def objective(trial: Trial) -> float:
            params = {}
            for key, bounds in self.param_config.items():
                low, high = bounds
                if isinstance(low, int) and isinstance(high, int):
                    params[key] = trial.suggest_int(key, low, high)
                elif isinstance(low, float) and isinstance(high, float):
                    params[key] = trial.suggest_float(key, low, high)
                elif isinstance(low, (list, tuple)):
                    params[key] = trial.suggest_categorical(key, list(low))
                else:
                    params[key] = low

            from backtest.backtest_runner import BacktestRunner

            try:
                runner = BacktestRunner()
                method = self._detect_runner_method(runner)
                metrics = method(data_path=self.data_path, params=params, strategy_name=self.strategy_name)
                if isinstance(metrics, dict) and "fitness" in metrics:
                    return float(metrics["fitness"])
                return 0.0
            except Exception as e:
                self.logger.error(f"Trial failed for params {params}: {e}")
                return 0.0

        study_name = f"{self.strategy_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        study = optuna.create_study(
            direction="maximize", study_name=study_name, sampler=optuna.samplers.TPESampler()
        )
        study.optimize(objective, n_trials=10, n_jobs=self.max_workers)

        best = study.best_trial
        self.logger.info(f"🏆 Best trial → Params: {best.params}, Fitness={best.value:.4f}")
        self._save_results([{"params": best.params, "fitness": best.value}], "bayesian")

    # ----------------------------------------------------------------------
    # Utilities
    # ----------------------------------------------------------------------
    def _safe_run(self, run_fn: Callable, params: Dict[str, Any]) -> Dict[str, Any]:
        """Safely run a backtest function with error handling."""
        try:
            result = run_fn(data_path=self.data_path, params=params, strategy_name=self.strategy_name)
            if isinstance(result, dict):
                result["params"] = params
            return result
        except Exception as e:
            self.logger.error(f"Execution error for {params}: {e}")
            return {}

    def _detect_runner_method(self, runner) -> Callable:
        for name in ["run_backtest", "run", "execute", "start", "run_all"]:
            if hasattr(runner, name):
                return getattr(runner, name)
        raise AttributeError("No compatible run method found in BacktestRunner")

    def _save_results(self, results: list[dict[str, Any]], mode: str) -> None:
        """Save aggregated optimization results."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        result_path = self.output_dir / f"{mode}_results_{timestamp}.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        self.logger.info(f"📊 Results saved → {result_path}")

    def _save_summary(self) -> Path:
        summary = {
            "strategy": self.strategy_name,
            "mode": self.mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_path": str(self.data_path),
            "param_config": self.param_config,
            "max_workers": self.max_workers,
        }
        summary_path = self.output_dir / f"optimization_summary_{self.mode}.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return summary_path


# ----------------------------------------------------------------------
# CLI Entry Point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("⚡ Running Parallel OptimizationRunner self-test...")

    try:
        mode = sys.argv[1].lower()
    except IndexError:
        mode = "grid"

    if mode == "grid":
        params = {"window": [10, 20], "threshold": [0.1, 0.2]}
    elif mode == "genetic":
        params = {"window": (5, 25), "threshold": (0.05, 0.25)}
    elif mode == "bayesian":
        params = {"window": (5, 25), "threshold": (0.05, 0.25)}
    else:
        print(f"❌ Unknown mode: {mode}")
        sys.exit(1)

    runner = OptimizationRunner(
        strategy_name="statistical_arbitrage",
        mode=mode,
        data_path=Path("data/cleaned/BTC_USD_1m_cleaned.csv"),
        param_config=params,
    )

    runner.run()
