# dashboard/inflation-dashboard.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from src.data_loader import load_all_series
from src.basis import build_swap_proxy, build_iota, compute_zscore
from src.backtest import run_backtest, compute_metrics

# Helper pour que cela fonctionne avec toutes les versions de MatPlotLib

def clean_spines(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Inflation Trading Desk — IOTA Monitor",
    page_icon="📈",
    layout="wide"
)

# ============================================================
# DATA LOADING (cached)
# ============================================================
@st.cache_data(ttl=3600)
def load_data():
    """Load and compute all series. Cached for 1 hour."""
    series   = load_all_series()
    swap     = build_swap_proxy(series["hicp"])
    iota     = build_iota(series["breakeven"], swap)
    zscore   = compute_zscore(iota)

    # Align everything
    idx = series["breakeven"].index\
            .intersection(swap.index)\
            .intersection(iota.index)\
            .intersection(zscore.index)

    return {
        "nominal"  : series["nominal"].loc[idx],
        "real"     : series["real"].loc[idx],
        "breakeven": series["breakeven"].loc[idx],
        "hicp"     : series["hicp"].loc[idx],
        "swap"     : swap.loc[idx],
        "iota"     : iota.loc[idx],
        "zscore"   : zscore.loc[idx],
    }


# ============================================================
# HEADER
# ============================================================
st.title("Inflation Trading Desk — IOTA Monitor")
st.caption("Euro Area 10Y Inflation Basis | Data: ECB Statistical Data Warehouse")

with st.spinner("Loading ECB data..."):
    data = load_data()

# Current values
last_date      = data["iota"].index[-1].strftime("%d %b %Y")
current_be     = data["breakeven"].iloc[-1]
current_iota   = data["iota"].iloc[-1]
current_z      = data["zscore"].iloc[-1]
current_nominal = data["nominal"].iloc[-1]
current_real   = data["real"].iloc[-1]

# Signal logic
if current_z > 2.0:
    signal_label = "SHORT BASIS"
    signal_color = "inverse"
elif current_z < -2.0:
    signal_label = "LONG BASIS"
    signal_color = "normal"
else:
    signal_label = "FLAT"
    signal_color = "off"

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.header("Parameters")
st.sidebar.markdown("---")

st.sidebar.subheader("Signal")
entry_thresh = st.sidebar.slider(
    "Entry threshold (σ)", 1.0, 3.0, 2.0, 0.1)
exit_band = st.sidebar.slider(
    "Exit band (σ)", 0.0, 1.0, 0.0, 0.1)
window = st.sidebar.slider(
    "Rolling window (days)", 60, 504, 252, 21)

st.sidebar.markdown("---")
st.sidebar.subheader("Stress Test")
shock_bps = st.sidebar.slider(
    "Breakeven shock (bps)", -100, 100, 0, 5)

st.sidebar.markdown("---")
st.sidebar.subheader("Date range")
start_year = st.sidebar.slider("Start year", 2004, 2024, 2004)

# Filter by date
mask = data["iota"].index.year >= start_year
iota_filtered = data["iota"][mask]
be_filtered   = data["breakeven"][mask]
nom_filtered  = data["nominal"][mask]
real_filtered = data["real"][mask]
hicp_filtered = data["hicp"][mask]
swap_filtered = data["swap"][mask]

# Recompute z-score with chosen window
zs_filtered = compute_zscore(iota_filtered, window=window)

# ============================================================
# PAGE TABS
# ============================================================
tab1, tab2, tab3 = st.tabs([
    "Live Monitor",
    "Backtest",
    "Stress Test"
])

# ============================================================
# TAB 1 — LIVE MONITOR
# ============================================================
with tab1:

    # KPI row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Nominal 10Y",  f"{current_nominal:.3f}%", delta=None)
    col2.metric("Real 10Y",     f"{current_real:.3f}%",    delta=None)
    col3.metric("Breakeven",    f"{current_be:.3f}%",
                delta=f"{(current_be - data['breakeven'].mean()):.3f}% vs mean")
    col4.metric("IOTA",         f"{current_iota*100:.1f} bps",
                delta=f"{(current_iota - data['iota'].mean())*100:.1f} bps vs mean")
    col5.metric("Signal",       signal_label)

    st.caption(f"Last data point: {last_date}")
    st.divider()

    # Chart 1 : Breakeven vs Swap
    st.subheader("Breakeven Bond vs Inflation Swap Proxy")
    fig1, ax1 = plt.subplots(figsize=(12, 3.5), dpi=120)
    ax1.plot(be_filtered.index,   be_filtered,   color='#006D19',
             linewidth=1.2, label='Breakeven Bond 10Y')
    ax1.plot(swap_filtered.index, swap_filtered, color='#003366',
             linewidth=1.2, linestyle='--', label='Swap Proxy 10Y')
    ax1.axhline(2.0, color='gray', linewidth=0.7,
                linestyle=':', label='ECB target 2%')
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax1.legend(frameon=False, fontsize=9)
    clean_spines(ax1)
    st.pyplot(fig1)
    plt.close()

    # Chart 2 : IOTA + Z-score
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("IOTA — Inflation Basis")
        fig2, ax2 = plt.subplots(figsize=(7, 3.5), dpi=120)
        ax2.plot(iota_filtered.index, iota_filtered * 100,
                 color='#CC3300', linewidth=1.0)
        ax2.axhline(data['iota'].mean() * 100, color='gray',
                    linewidth=0.8, linestyle='--',
                    label=f"Mean = {data['iota'].mean()*100:.1f} bps")
        ax2.axhline(0, color='black', linewidth=0.4)
        ax2.fill_between(iota_filtered.index, 0, iota_filtered * 100,
                         where=(iota_filtered > 0),
                         alpha=0.12, color='#CC3300')
        ax2.set_ylabel('IOTA (bps)')
        ax2.legend(frameon=False, fontsize=9)
        clean_spines(ax2)
        st.pyplot(fig2)
        plt.close()

    with col_b:
        st.subheader("Z-score — Trading Signal")
        fig3, ax3 = plt.subplots(figsize=(7, 3.5), dpi=120)
        ax3.plot(zs_filtered.index, zs_filtered,
                 color='#003366', linewidth=1.0)
        ax3.axhline( entry_thresh, color='#CC3300',
                    linewidth=1.0, linestyle='--',
                    label=f'Sell +{entry_thresh}σ')
        ax3.axhline(-entry_thresh, color='#006D19',
                    linewidth=1.0, linestyle='--',
                    label=f'Buy -{entry_thresh}σ')
        ax3.axhline(0, color='gray', linewidth=0.4)
        ax3.fill_between(zs_filtered.index, entry_thresh, zs_filtered,
                         where=(zs_filtered > entry_thresh),
                         alpha=0.2, color='#CC3300')
        ax3.fill_between(zs_filtered.index, -entry_thresh, zs_filtered,
                         where=(zs_filtered < -entry_thresh),
                         alpha=0.2, color='#006D19')
        ax3.set_ylim(-4, 4)
        ax3.set_ylabel('Z-score (σ)')
        ax3.legend(frameon=False, fontsize=9)
        clean_spines(ax3)
        st.pyplot(fig3)
        plt.close()

# ============================================================
# TAB 2 — BACKTEST
# ============================================================
with tab2:
    st.subheader("Strategy Backtest — IOTA Mean Reversion")
    st.caption(f"Parameters: window={window}d | entry=±{entry_thresh}σ | exit=±{exit_band}σ")

    # Run backtest
    bt = run_backtest(iota_filtered, zs_filtered,
                      entry=entry_thresh,
                      exit_band=exit_band)
    metrics = compute_metrics(bt)

    # Metrics row
    cols = st.columns(len(metrics))
    for col, (k, v) in zip(cols, metrics.items()):
        col.metric(k, v)

    st.divider()

    # P&L chart
    st.subheader("Cumulative P&L (bps)")
    fig4, axes4 = plt.subplots(2, 1, figsize=(12, 6), dpi=120, sharex=True)

    axes4[0].plot(bt['cum_pnl'].index, bt['cum_pnl'] * 100,
                  color='#003366', linewidth=1.2, label='Cumulative P&L')
    axes4[0].axhline(0, color='gray', linewidth=0.4)
    axes4[0].set_ylabel('P&L (bps)')
    axes4[0].legend(frameon=False, fontsize=9)
    clean_spines(axes4[0])
    axes4[1].fill_between(bt['drawdown'].index, bt['drawdown'] * 100, 0,
                          color='#CC3300', alpha=0.6, label='Drawdown')
    axes4[1].set_ylabel('Drawdown (bps)')
    axes4[1].legend(frameon=False, fontsize=9)
    clean_spines(axes4[1])

    plt.tight_layout()
    st.pyplot(fig4)
    plt.close()

# ============================================================
# TAB 3 — STRESS TEST
# ============================================================
with tab3:
    st.subheader("Stress Test — Breakeven Shock")
    st.write(f"Simulating a **{shock_bps:+d} bps** shock on the current breakeven rate.")

    shocked_be   = current_be   + shock_bps / 100
    shocked_iota = current_iota - shock_bps / 100
    shocked_z    = (shocked_iota - data['iota'].rolling(window).mean().iloc[-1]) / \
                    data['iota'].rolling(window).std().iloc[-1]

    # KPIs post-shock
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Breakeven (shocked)",
                f"{shocked_be:.3f}%",
                delta=f"{shock_bps:+d} bps")
    col2.metric("IOTA (shocked)",
                f"{shocked_iota*100:.1f} bps",
                delta=f"{(shocked_iota - current_iota)*100:+.1f} bps")
    col3.metric("Z-score (shocked)",
                f"{shocked_z:.2f}σ",
                delta=f"{shocked_z - current_z:+.2f}σ")

    # Signal post-shock
    if shocked_z > entry_thresh:
        new_signal = "SHORT BASIS"
    elif shocked_z < -entry_thresh:
        new_signal = "LONG BASIS"
    else:
        new_signal = "FLAT"
    col4.metric("Signal (shocked)", new_signal)

    st.divider()

    # Scenario table
    st.subheader("Scenario Analysis")
    shocks = [-100, -75, -50, -25, -10, 0, 10, 25, 50, 75, 100]
    rows   = []
    for s in shocks:
        be_s    = current_be + s / 100
        iota_s  = current_iota - s / 100
        z_s     = (iota_s - data['iota'].rolling(window).mean().iloc[-1]) / \
                   data['iota'].rolling(window).std().iloc[-1]
        if z_s > entry_thresh:   sig = "SHORT"
        elif z_s < -entry_thresh: sig = "LONG"
        else:                     sig = "FLAT"
        rows.append({
            "Shock (bps)"       : f"{s:+d}",
            "Breakeven (%)"     : f"{be_s:.3f}",
            "IOTA (bps)"        : f"{iota_s*100:.1f}",
            "Z-score (σ)"       : f"{z_s:.2f}",
            "Signal"            : sig,
        })

    df_scenarios = pd.DataFrame(rows)
    st.dataframe(df_scenarios, use_container_width=True, hide_index=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(
    "Data source: ECB Statistical Data Warehouse · "
    "Nominal yield: YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y · "
    "Real yield: FM/M.U2.EUR.4F.BB.R_U2_10Y.YLDA · "
    "HICP: ICP/M.U2.N.000000.4.ANR"
)


