# /optimization/optimizers/utils.py

"""
NEXORA Optimizer Utilities
--------------------------
Shared helper functions for parameter grid generation,
performance metric evaluation, and result management
across optimization strategies.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


# -------------------------------------------------------------------------
# Parameter Grid Utilities
# -------------------------------------------------------------------------
def generate_param_grid(param_space: Dict[str, Iterable[Any]]) -> List[Dict[str, Any]]:
    """
    Generate a full Cartesian parameter grid from a dictionary of parameter ranges.

    Example:
        >>> generate_param_grid({"lr": [0.001, 0.01], "batch": [16, 32]})
        [{'lr': 0.001, 'batch': 16}, {'lr': 0.001, 'batch': 32},
         {'lr': 0.01, 'batch': 16}, {'lr': 0.01, 'batch': 32}]
    """
    if not param_space:
        raise ValueError("Parameter space cannot be empty.")

    keys = list(param_space.keys())
    values = list(param_space.values())

    grid = [dict(zip(keys, combination)) for combination in itertools.product(*values)]
    return grid


# -------------------------------------------------------------------------
# Metric Evaluation
# -------------------------------------------------------------------------
def compute_fitness(metric_dict: Dict[str, float], target_metric: str = "sharpe_ratio") -> float:
    """
    Compute fitness score based on a given performance metric.
    Falls back to a safe value if the target metric is missing or invalid.

    Args:
        metric_dict: Dictionary of performance metrics (e.g., {"sharpe_ratio": 1.5})
        target_metric: Key to use for fitness evaluation

    Returns:
        Fitness score as a float
    """
    value = metric_dict.get(target_metric, 0.0)
    if not isinstance(value, (int, float)):
        return 0.0
    return float(value)


# -------------------------------------------------------------------------
# Result Management
# -------------------------------------------------------------------------
def sort_results(results: List[Dict[str, Any]], key: str = "sharpe_ratio") -> List[Dict[str, Any]]:
    """
    Sort optimization results by a chosen metric, descending.
    Returns an empty list if the input is invalid.
    """
    if not results:
        return []

    try:
        sorted_results = sorted(results, key=lambda x: x.get(key, 0.0), reverse=True)
        return sorted_results
    except Exception:
        return results


def save_json(data: Any, path: Path) -> None:
    """
    Save arbitrary Python data (list, dict, etc.) as formatted JSON.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(path: Path) -> Dict[str, Any]:
    """
    Load a JSON file safely and return its contents.
    Returns an empty dict on error.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# -------------------------------------------------------------------------
# Parameter Serialization Helpers
# -------------------------------------------------------------------------
def param_tuple(param_dict: Dict[str, Any]) -> Tuple[Any, ...]:
    """
    Convert a parameter dictionary into a tuple (sorted by key)
    for use in caching or hashing operations.
    """
    return tuple(param_dict[k] for k in sorted(param_dict.keys()))

# -------------------------------------------------------------------------
# Quick interactive test
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print("🔧 Running utils self-test...")

    param_space = {"lr": [0.001, 0.01], "batch": [16, 32]}
    grid = generate_param_grid(param_space)
    print(f"Generated {len(grid)} parameter combinations:")
    for g in grid:
        print("  ", g)

    metrics = {"sharpe_ratio": 1.42, "sortino": 1.21}
    fitness = compute_fitness(metrics)
    print(f"\nComputed fitness (Sharpe): {fitness}")

    results = [
        {"params": {"lr": 0.001}, "sharpe_ratio": 1.1},
        {"params": {"lr": 0.01}, "sharpe_ratio": 1.9},
        {"params": {"lr": 0.005}, "sharpe_ratio": 1.4},
    ]
    sorted_results = sort_results(results)
    print("\nTop result:")
    print(sorted_results[0])

    test_path = Path("logs/test_utils_output.json")
    save_json(results, test_path)
    print(f"\n✅ Saved JSON test output to {test_path.resolve()}")
