# src/backtest.py
import pandas as pd
import numpy as np


def run_backtest(iota: pd.Series,
                 zscore: pd.Series,
                 entry: float = 2.0,
                 exit_band: float = 0.0,
                 transaction_cost_bps: float = 5.0) -> pd.DataFrame:
    """
    Run the IOTA mean-reversion backtest.
    Returns a DataFrame with position, P&L, cumulative P&L and drawdown.
    """
    tc = transaction_cost_bps / 10_000

    df = pd.DataFrame({"iota": iota, "zscore": zscore}).dropna()
    pos = pd.Series(0, index=df.index, dtype=float)
    cp  = 0

    for i in range(1, len(df)):
        z = df["zscore"].iloc[i]
        if cp == 0:
            if z < -entry:  cp =  1
            elif z > entry: cp = -1
        elif cp == 1:
            if z > -exit_band: cp = 0
        elif cp == -1:
            if z <  exit_band: cp = 0
        pos.iloc[i] = cp

    df["position"] = pos
    df["iota_chg"] = df["iota"].diff()
    df["pnl_raw"]  = df["position"].shift(1) * df["iota_chg"]
    df["trade"]    = df["position"].diff().abs()
    df["pnl_net"]  = df["pnl_raw"] - df["trade"] * tc
    df["cum_pnl"]  = df["pnl_net"].cumsum()
    df["drawdown"] = df["cum_pnl"] - df["cum_pnl"].cummax()

    return df


def compute_metrics(df: pd.DataFrame) -> dict:
    """Compute summary performance metrics from backtest DataFrame."""
    ann_ret = df["pnl_net"].mean() * 252
    ann_vol = df["pnl_net"].std()  * np.sqrt(252)
    sharpe  = ann_ret / ann_vol if ann_vol > 0 else 0
    max_dd  = df["drawdown"].min()
    n_trades = int((df["trade"] > 0).sum() // 2)
    total_pnl = df["pnl_net"].sum()

    return {
        "Annual Return (bps)" : round(ann_ret  * 100, 1),
        "Annual Vol (bps)"    : round(ann_vol  * 100, 1),
        "Sharpe Ratio"        : round(sharpe, 3),
        "Max Drawdown (bps)"  : round(max_dd  * 100, 1),
        "Total P&L (bps)"     : round(total_pnl * 100, 1),
        "Nb Trades"           : n_trades,
    }