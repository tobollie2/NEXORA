# test_meta_agent.py
import pandas as pd
import numpy as np
import yaml

from ai.meta_agent import MetaAgent
from strategies.trend_following import TrendFollowingStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.statistical_arbitrage import StatisticalArbitrageStrategy

# Load config
cfg = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))

# Initialize MetaAgent with three strategies
meta = MetaAgent(
    {
        "TrendFollowing": TrendFollowingStrategy,
        "MeanReversion": MeanReversionStrategy,
        "StatArb": StatisticalArbitrageStrategy,
    },
    cfg,
)

# Generate synthetic market data for testing
prices = pd.Series(10000 + np.cumsum(np.random.normal(0, 15, 1000)))

# Simulate 10 episodes
for ep in range(10):
    data = {"prices": prices, "returns": prices.pct_change().dropna()}
    rewards = meta.evaluate_agents(data)
    meta.update_allocation(rewards)
    print(f"Episode {ep:02d} | {meta.summary_str()}")
