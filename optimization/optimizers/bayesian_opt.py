# /optimization/optimizers/bayesian_opt.py
from skopt import gp_minimize
from skopt.space import Real, Integer, Categorical


class BayesianOptimizer:
    """Bayesian optimization via scikit-optimize."""

    def _convert_space(self, param_space):
        space = []
        for k, v in param_space.items():
            if all(isinstance(i, (int, float)) for i in v):
                bounds = (min(v), max(v))
                space.append(
                    Real(*bounds, name=k)
                    if any(isinstance(i, float) for i in v)
                    else Integer(*bounds, name=k)
                )
            else:
                space.append(Categorical(v, name=k))
        return space

    def run(self, objective_fn, param_space, max_iter=50):
        space = self._convert_space(param_space)

        def wrapped(params):
            p = {dim.name: val for dim, val in zip(space, params)}
            return objective_fn(p)

        result = gp_minimize(wrapped, space, n_calls=max_iter, random_state=42)
        best_params = {space[i].name: result.x[i] for i in range(len(space))}
        return best_params, result.fun
