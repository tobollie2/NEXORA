# /ai/reward_functions.py
def sharpe_based_reward(results: dict) -> float:
    """Compute reward based on Sharpe ratio and drawdown."""
    sharpe = results.get("sharpe", 0)
    drawdown = results.get("max_drawdown", 0)
    return sharpe - (drawdown * 0.1)


def total_return_reward(results: dict) -> float:
    return results.get("total_return", 0)
