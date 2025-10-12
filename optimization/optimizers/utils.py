# /optimization/optimizers/utils.py
import traceback


def safe_objective(objective_fn, params):
    try:
        return objective_fn(params)
    except Exception:
        traceback.print_exc()
        return 1e9
