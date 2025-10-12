# /strategies/statistical_arbitrage_cluster.py
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint

from ai.cointegration.johansen_module import JohansenCointegration


class StatArbCluster:
    """
    Statistical Arbitrage Cluster Engine
    ------------------------------------
    Detects cointegrated asset groups using adaptive methodology:
        - Engle–Granger for pairs
        - Johansen for 3+ assets

    Filters clusters based on cointegration rank strength and returns
    diagnostic statistics useful for portfolio construction or further
    meta-learning.
    """

    def __init__(self, p_threshold: float = 0.05, min_rank: int = 1, max_assets: int = 6):
        """
        Parameters
        ----------
        p_threshold : float
            Significance level for Engle–Granger test.
        min_rank : int
            Minimum rank for Johansen clusters to be considered valid.
        max_assets : int
            Maximum assets allowed per cluster for stability.
        """
        self.p_threshold = p_threshold
        self.min_rank = min_rank
        self.max_assets = max_assets

    # ------------------------------------------------------------------
    # Core detection
    # ------------------------------------------------------------------
    def _find_cointegrated_groups(self, prices: pd.DataFrame) -> dict:
        """
        Automatically switch between Engle–Granger (pairwise)
        and Johansen (multivariate) depending on number of assets.
        """
        n_assets = len(prices.columns)
        if n_assets == 2:
            # --- Engle–Granger ---
            try:
                _, pval, _ = coint(prices.iloc[:, 0], prices.iloc[:, 1])
                return {
                    "method": "Engle-Granger",
                    "rank": 1 if pval < self.p_threshold else 0,
                    "pvalue": float(pval),
                }
            except Exception as e:
                return {
                    "method": "Engle-Granger",
                    "rank": 0,
                    "pvalue": 1.0,
                    "error": str(e),
                }

        elif n_assets >= 3:
            # --- Johansen ---
            try:
                joh = JohansenCointegration()
                joh.fit(prices)
                summary = joh.summary()
                summary["method"] = "Johansen"
                return summary
            except Exception as e:
                return {"method": "Johansen", "rank": 0, "pvalue": 1.0, "error": str(e)}

        return {"method": "N/A", "rank": 0, "pvalue": 1.0}

    # ------------------------------------------------------------------
    # Cluster scoring
    # ------------------------------------------------------------------
    def _cluster_score(self, result: dict) -> float:
        """
        Compute a normalized confidence score for the cluster.
        Higher = stronger cointegration.
        """
        if result["method"] == "Engle-Granger":
            return max(0.0, 1.0 - result.get("pvalue", 1.0))
        elif result["method"] == "Johansen":
            rank = result.get("rank", 0)
            return min(1.0, rank / 3.0)  # simple normalization
        return 0.0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def evaluate_cluster(self, prices: pd.DataFrame) -> dict:
        """
        Evaluate a single cluster of price series and compute
        cointegration diagnostics, validity, and score.
        """
        result = self._find_cointegrated_groups(prices)
        score = self._cluster_score(result)
        result["score"] = round(score, 3)
        result["valid"] = (result["method"] == "Engle-Granger" and result["rank"] == 1) or (
            result["method"] == "Johansen" and result["rank"] >= self.min_rank
        )
        return result

    def filter_valid_clusters(self, cluster_dict: dict) -> dict:
        """
        Filter multiple candidate clusters and return only those
        with strong cointegration signals.
        """
        valid_clusters = {}
        for name, data in cluster_dict.items():
            if isinstance(data, pd.DataFrame) and data.shape[1] <= self.max_assets:
                res = self.evaluate_cluster(data)
                if res["valid"]:
                    valid_clusters[name] = res
        return valid_clusters

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def summary_str(self, result: dict) -> str:
        """
        Pretty-print result of a single cluster evaluation.
        """
        return (
            f"[{result.get('method','?')}]  "
            f"Rank={result.get('rank',0)}  "
            f"Score={result.get('score',0):.2f}  "
            f"Valid={result.get('valid',False)}"
        )


# ----------------------------------------------------------------------
# Quick self-test
# ----------------------------------------------------------------------
if __name__ == "__main__":
    np.random.seed(42)
    x = np.cumsum(np.random.normal(0, 1, 400))
    y = x + np.random.normal(0, 0.4, 400)
    z = 0.5 * x + 0.2 * y + np.random.normal(0, 0.3, 400)
    df = pd.DataFrame({"x": x, "y": y, "z": z})

    cluster = StatArbCluster()
    result = cluster.evaluate_cluster(df)
    print(cluster.summary_str(result))
