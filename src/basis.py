# src/basis.py
import pandas as pd
import numpy as np


ECB_TARGET = 2.0
LAMBDA     = 0.6


def build_swap_proxy(hicp: pd.Series,
                     lambda_: float = LAMBDA,
                     ecb_target: float = ECB_TARGET,
                     window: int = 252) -> pd.Series:
    """Build a synthetic ZC inflation swap proxy."""
    hicp_trailing = hicp.rolling(window, min_periods=60).mean()
    return (1 - lambda_) * hicp_trailing + lambda_ * ecb_target


def build_iota(breakeven: pd.Series,
               swap_proxy: pd.Series) -> pd.Series:
    """Compute IOTA = Swap Proxy − Breakeven Bond."""
    idx = breakeven.index.intersection(swap_proxy.index)
    return swap_proxy.loc[idx] - breakeven.loc[idx]


def compute_zscore(series: pd.Series,
                   window: int = 252) -> pd.Series:
    """Rolling z-score."""
    roll_mean = series.rolling(window, min_periods=60).mean()
    roll_std  = series.rolling(window, min_periods=60).std()
    return (series - roll_mean) / roll_std


def get_signal(zscore: float,
               entry: float = 2.0,
               exit_band: float = 0.0,
               current_pos: int = 0) -> int:
    """
    Returns position signal.
    +1 = long basis, -1 = short basis, 0 = flat
    """
    if current_pos == 0:
        if zscore < -entry:  return  1
        if zscore >  entry:  return -1
    elif current_pos == 1:
        if zscore > -exit_band: return 0
    elif current_pos == -1:
        if zscore <  exit_band: return 0
    return current_pos