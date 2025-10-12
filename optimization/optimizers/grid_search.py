# /optimization/optimizers/grid_search.py
from itertools import product


class GridSearchOptimizer:
    """Exhaustive grid search optimizer."""

    def run(self, objective_fn, param_space, max_iter=None):
        keys = list(param_space.keys())
        combos = list(product(*param_space.values()))
        if max_iter:
            combos = combos[:max_iter]

        best_score = float("inf")
        best_params = None

        for combo in combos:
            params = dict(zip(keys, combo))
            score = objective_fn(params)
            if score < best_score:
                best_score, best_params = score, params

        return best_params, best_score
