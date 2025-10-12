"""
optimization/optimizers/genetic_opt.py
-------------------------------------
Genetic algorithm optimizer for trading strategy parameter tuning.

This optimizer evolves a population of parameter sets over multiple generations,
adapting to whichever backtest execution API is exposed by BacktestRunner.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from backtest.backtest_runner import BacktestRunner
from monitoring.logging_utils import setup_logger


class GeneticOptimizer:
    """
    Evolves strategy parameter sets using a genetic algorithm.
    Compatible with different BacktestRunner APIs.
    """

    def __init__(
        self,
        strategy_name: str,
        param_bounds: Dict[str, Tuple[Any, Any]],
        data_path: Path,
        population_size: int = 10,
        generations: int = 5,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        seed: int = 42,
    ) -> None:
        self.strategy_name = strategy_name
        self.param_bounds = param_bounds
        self.data_path = data_path
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.random = random.Random(seed)
        self.logger = setup_logger(f"GeneticOptimizer[{strategy_name}]")

    # ---------------------- Population management ----------------------

    def initialize_population(self) -> List[Dict[str, Any]]:
        """Randomly initialize parameter sets within given bounds."""
        pop: List[Dict[str, Any]] = []
        for _ in range(self.population_size):
            individual = {
                key: self._random_value(bounds) for key, bounds in self.param_bounds.items()
            }
            pop.append(individual)
        return pop

    def _random_value(self, bounds: Tuple[Any, Any]) -> Any:
        """Generate a random value between lower and upper bounds."""
        low, high = bounds
        if isinstance(low, int) and isinstance(high, int):
            return self.random.randint(low, high)
        if isinstance(low, float) and isinstance(high, float):
            return self.random.uniform(low, high)
        if isinstance(low, (list, tuple)):
            return self.random.choice(low)
        return low

    # ---------------------- Backtest integration ----------------------

    def _get_runner_method(self, runner: BacktestRunner):
        """Detect the available run method on BacktestRunner."""
        for name in ["run_backtest", "run", "execute", "start", "run_all"]:
            if hasattr(runner, name):
                self.logger.info(f"⚙️ Using BacktestRunner.{name}()")
                return getattr(runner, name)
        raise AttributeError(
            "BacktestRunner has no supported run method (expected one of: "
            "run_backtest, run, execute, start, run_all)"
        )

    def evaluate_fitness(self, params: Dict[str, Any]) -> float:
        """Run a backtest and return the fitness score."""
        try:
            runner = BacktestRunner()
            run_fn = self._get_runner_method(runner)

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

            if isinstance(metrics, dict) and "fitness" in metrics:
                return float(metrics["fitness"])
            return 0.0
        except Exception as e:
            self.logger.error(f"❌ Fitness evaluation failed for {params}: {e}")
            return 0.0

    # ---------------------- Genetic algorithm core ----------------------

    def select_parents(self, population: List[Dict[str, Any]], fitnesses: List[float]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Select two parents using fitness-proportional (roulette) selection."""
        total_fitness = sum(fitnesses)
        if total_fitness == 0:
            return self.random.choice(population), self.random.choice(population)
        probs = [f / total_fitness for f in fitnesses]
        parent1 = self.random.choices(population, weights=probs, k=1)[0]
        parent2 = self.random.choices(population, weights=probs, k=1)[0]
        return parent1, parent2

    def crossover(self, p1: Dict[str, Any], p2: Dict[str, Any]) -> Dict[str, Any]:
        """Perform single-point crossover between two parents."""
        child = {}
        for key in self.param_bounds.keys():
            child[key] = p1[key] if self.random.random() < 0.5 else p2[key]
        return child

    def mutate(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """Apply random mutation within parameter bounds."""
        for key, bounds in self.param_bounds.items():
            if self.random.random() < self.mutation_rate:
                individual[key] = self._random_value(bounds)
        return individual

    # ---------------------- Main optimization loop ----------------------

    def run(self) -> None:
        """Execute the full genetic optimization process."""
        self.logger.info(f"🚀 Starting genetic optimization for '{self.strategy_name}'")
        population = self.initialize_population()

        best_individual: Dict[str, Any] | None = None
        best_fitness: float = 0.0

        for generation in range(1, self.generations + 1):
            self.logger.info(f"🧬 Generation {generation}/{self.generations}")

            fitnesses = [self.evaluate_fitness(ind) for ind in population]
            gen_best_idx = int(max(range(len(fitnesses)), key=lambda i: fitnesses[i]))
            gen_best = population[gen_best_idx]
            gen_best_fit = fitnesses[gen_best_idx]

            if gen_best_fit > best_fitness:
                best_fitness = gen_best_fit
                best_individual = gen_best.copy()

            self.logger.info(f"🏆 Best fitness this gen: {gen_best_fit:.4f}")

            # Create next generation
            next_population: List[Dict[str, Any]] = []
            while len(next_population) < self.population_size:
                parent1, parent2 = self.select_parents(population, fitnesses)
                if self.random.random() < self.crossover_rate:
                    child = self.crossover(parent1, parent2)
                else:
                    child = parent1.copy()
                child = self.mutate(child)
                next_population.append(child)

            population = next_population

        # Save results
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = Path("logs/optimization_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"genetic_results_{timestamp}.json"

        results = {"best_params": best_individual, "best_fitness": best_fitness}
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        self.logger.info(f"🎯 Genetic optimization complete. Best fitness={best_fitness:.4f}")
        self.logger.info(f"📁 Results saved → {output_file}")


if __name__ == "__main__":
    print("🧬 Running GeneticOptimizer self-test...")

    param_bounds = {
        "window": (5, 30),
        "threshold": (0.05, 0.25),
    }

    optimizer = GeneticOptimizer(
        strategy_name="statistical_arbitrage",
        param_bounds=param_bounds,
        data_path=Path("data/cleaned/BTC_USD_1m_cleaned.csv"),
        population_size=6,
        generations=3,
        mutation_rate=0.2,
        crossover_rate=0.7,
    )

    optimizer.run()
