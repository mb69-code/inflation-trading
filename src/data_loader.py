# src/data_loader.py
import pandas as pd
import numpy as np
import requests
from io import StringIO


def fetch_ecb_series(dataflow: str, series_key: str,
                     start: str = "2004-01-01") -> pd.Series:
    """Fetch a daily time series from the ECB Data Portal API."""
    url = (
        f"https://data-api.ecb.europa.eu/service/data/"
        f"{dataflow}/{series_key}?format=csvdata&startPeriod={start}"
    )
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text))
    df = df[["TIME_PERIOD", "OBS_VALUE"]].copy()
    df["TIME_PERIOD"] = pd.to_datetime(df["TIME_PERIOD"])
    df = df.set_index("TIME_PERIOD").sort_index()
    df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    return df["OBS_VALUE"]


def load_all_series() -> dict:
    """
    Load and clean all required series from ECB.
    Returns a dict of cleaned pandas Series.
    """
    # Nominal 10Y
    nominal = fetch_ecb_series("YC", "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y")

    # Real 10Y (monthly → interpolated daily)
    real_monthly = fetch_ecb_series("FM", "M.U2.EUR.4F.BB.R_U2_10Y.YLDA")
    real = real_monthly.resample("B").interpolate(method="linear")

    # HICP YoY
    hicp_monthly = fetch_ecb_series("ICP", "M.U2.N.000000.4.ANR")
    hicp = hicp_monthly.resample("B").interpolate(method="linear")

    # Align
    idx = nominal.index.intersection(real.index).intersection(hicp.index)
    nominal = nominal.loc[idx]
    real     = real.loc[idx]
    hicp     = hicp.loc[idx]

    # Clean real yield (remove ECB data anomalies)
    real_clean = real.copy()
    real_clean[(real_clean < -2.0) | (real_clean > 4.0)] = np.nan
    real_clean = real_clean.interpolate(method="linear")

    # Breakeven
    breakeven = nominal - real_clean

    return {
        "nominal"  : nominal,
        "real"     : real_clean,
        "hicp"     : hicp,
        "breakeven": breakeven,
    }