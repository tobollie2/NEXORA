# /ai/cointegration/johansen_module.py
import numpy as np
import pandas as pd
from statsmodels.tsa.vector_ar.vecm import coint_johansen


class JohansenCointegration:
    """
    Johansen Cointegration Analysis
    --------------------------------
    Tests for multiple cointegrating relationships in multivariate
    time series. Returns eigenvalues, eigenvectors, and significance stats.
    """

    def __init__(self, det_order=0, k_ar_diff=1, significance=0.05):
        """
        det_order : int
            Deterministic trend assumption (0 = none, 1 = constant, etc.)
        k_ar_diff : int
            Number of lag differences to include in the VECM.
        significance : float
            Threshold for cointegration rank selection.
        """
        self.det_order = det_order
        self.k_ar_diff = k_ar_diff
        self.significance = significance
        self.result = None

    def fit(self, data: pd.DataFrame):
        """Run Johansen cointegration test on multivariate data."""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")

        if data.shape[1] < 3:
            raise ValueError("Johansen test requires 3 or more series")

        self.result = coint_johansen(data, self.det_order, self.k_ar_diff)
        return self.result

    def rank(self):
        """Estimate cointegration rank (number of stationary linear combinations)."""
        if self.result is None:
            raise RuntimeError("Must call .fit() before .rank()")

        trace_stat = self.result.lr1
        crit_values = self.result.cvt[:, [1]]  # 5% column
        rank = np.sum(trace_stat > crit_values.flatten())
        return int(rank)

    def cointegrating_vectors(self):
        """Return the eigenvectors corresponding to the cointegrating relationships."""
        if self.result is None:
            raise RuntimeError("Must call .fit() before accessing vectors")
        return pd.DataFrame(
            self.result.evec,
            columns=[f"vec_{i}" for i in range(self.result.evec.shape[1])],
        )

    def summary(self):
        """Return a summary dictionary."""
        if self.result is None:
            return {}
        return {
            "rank": self.rank(),
            "trace_stats": self.result.lr1.tolist(),
            "crit_values_5pct": self.result.cvt[:, 1].tolist(),
            "eigenvectors": self.cointegrating_vectors().to_dict(orient="list"),
        }
