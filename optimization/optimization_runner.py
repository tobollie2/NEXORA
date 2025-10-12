# optimization/optimization_runner.py  (Integrated)
import os
import yaml
import logging
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from optimization.optimizers.grid_search import GridSearchOptimizer
from optimization.optimizers.bayesian_opt import BayesianOptimizer
from optimization.optimizers.genetic_opt import GeneticOptimizer


class OptimizationRunner:
    """Unified multi-engine optimization controller."""

    def __init__(self, config_path: str = "config/settings.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.output_dir = os.path.join("reports", "optimization")
        os.makedirs(self.output_dir, exist_ok=True)

        self.engine_type = (
            self.config.get("optimization", {}).get("engine", "grid").lower()
        )
        self.max_iter = self.config.get("optimization", {}).get("max_iterations", 50)
        self.parallel = self.config.get("optimization", {}).get("parallel", True)
        self.metric_target = self.config.get("optimization", {}).get(
            "metric_target", "sharpe"
        )

        self.optimizer = self._load_engine(self.engine_type)
        self.all_logs = []  # store per-evaluation results

    def _load_engine(self, engine: str):
        return {
            "grid": GridSearchOptimizer,
            "bayesian": BayesianOptimizer,
            "genetic": GeneticOptimizer,
        }.get(engine, GridSearchOptimizer)()

    def optimize_strategy(self, strategy_cls, asset: str):
        strategy = strategy_cls(asset=asset, config=self.config)
        param_space = strategy.parameter_grid()

        def objective(params):
            try:
                result_df, metrics = strategy.run_backtest(params)
                score = -metrics.get(self.metric_target, 0.0)
                log_entry = {**params, "score": -score}
                self.all_logs.append(log_entry)
                return score
            except Exception as e:
                logging.exception(f"Error evaluating {params}: {e}")
                return 1e9

        best_params, best_score = self.optimizer.run(
            objective, param_space, self.max_iter
        )

        log_path = os.path.join(
            self.output_dir, f"{strategy_cls.__name__}_{asset}_log.csv"
        )
        pd.DataFrame(self.all_logs).to_csv(log_path, index=False)

        summary = {
            "strategy": strategy_cls.__name__,
            "asset": asset,
            "engine": self.engine_type,
            "metric": self.metric_target,
            "best_score": -best_score,
            "best_params": best_params,
            "log_file": log_path,
        }

        return summary

    def run_all(self, strategies, assets):
        jobs = [(s, a) for s in strategies for a in assets]
        logging.info(
            f"Running optimization on {len(jobs)} jobs using {self.engine_type} engine."
        )

        if self.parallel:
            with ThreadPoolExecutor() as ex:
                results = list(ex.map(lambda sa: self.optimize_strategy(*sa), jobs))
        else:
            results = [self.optimize_strategy(s, a) for s, a in jobs]

        summary_df = pd.DataFrame(results)
        summary_path = os.path.join(self.output_dir, "optimization_summary.csv")
        summary_df.to_csv(summary_path, index=False)

        # Save best configurations globally
        best_config = {
            row["strategy"]: {
                "asset": row["asset"],
                "best_params": row["best_params"],
                "best_score": row["best_score"],
            }
            for _, row in summary_df.iterrows()
        }
        yaml_path = os.path.join(self.output_dir, "best_params.yaml")
        with open(yaml_path, "w") as f:
            yaml.safe_dump(best_config, f)

        logging.info(f"Optimization completed. Summary CSV → {summary_path}")
        logging.info(f"Best parameters saved → {yaml_path}")
        return summary_df
