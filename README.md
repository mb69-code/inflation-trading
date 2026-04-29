
# Inflation Trading — IOTA Monitor

> End-to-end inflation basis trading framework: data pipeline, signal generation,
> backtesting, and interactive dashboard — built on live ECB data.

## Live Dashboard

**[Launch the interactive dashboard](https://inflation-trading.streamlit.app)**

No installation required, it runs directly in your browser !!


## Overview

This project models the **IOTA spread** — the basis between euro area ZC inflation
swap rates and bond-implied breakeven inflation. The IOTA captures a persistent
wedge between two instruments that theoretically price the same inflation expectations,
but diverge due to liquidity premia, indexation lags, and technical flows.

$$IOTA_t = \text{Swap}_{proxy}(t) - BE_{bond}(t) = \text{Swap}_{proxy}(t) - (y_{nominal} - y_{real})$$

**Trading logic:** The IOTA is mean-reverting over medium-term horizons.
A z-score above +2σ signals the swap market over-prices inflation relative
to the bond market → sell basis. Below -2σ → buy basis.



## Architecture

```
inflation-trading/
├── notebooks/
│   └── iota_trading_strategy.ipynb   # Full research pipeline
│   └── zc-inflation-swap-model.ipynb # Enhanced zcis curve model
├── src/
│   ├── data_loader.py               # ECB API — nominal, real, HICP
│   ├── basis.py                     # Swap proxy, IOTA, z-score
│   └── backtest.py                  # Backtest engine & metrics
├── dashboard/
│   └── inflation-dashboard.py       # Streamlit interactive monitor
├── data/                            # Generated charts & outputs
├── requirements.txt
└── README.md
```

---

## Methodology

### Data sources (ECB Statistical Data Warehouse)

| Series | Dataflow | Frequency | Description |
|---|---|---|---|
| Nominal 10Y | `YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y` | Daily | Euro area AAA govt bonds (Svensson) |
| Real 10Y | `FM/M.U2.EUR.4F.BB.R_U2_10Y.YLDA` | Monthly → interpolated | Inflation-linked benchmark |
| HICP YoY | `ICP/M.U2.N.000000.4.ANR` | Monthly → interpolated | Euro area realized inflation |

### Breakeven construction

$$BE_{bond} = y_{nominal} - y_{real}$$

### Swap proxy

Since euro area ZC swap rates are not publicly available, we construct a
synthetic proxy blending realized inflation momentum and the ECB long-term anchor:

$$\text{Swap}_{proxy}(t) = (1-\lambda) \cdot \bar{\pi}_{252d}(t) + \lambda \cdot \pi^*_{ECB}$$

with $\lambda = 0.6$ and $\pi^*_{ECB} = 2\%$.

### Signal

$$z_t = \frac{IOTA_t - \mu_{252d}}{\sigma_{252d}}$$

| Z-score | Signal | Action |
|---|---|---|
| $z > +2\sigma$ | SHORT basis | Sell swap, buy breakeven |
| $z < -2\sigma$ | LONG basis | Buy swap, sell breakeven |
| $\|z\| < 0.5\sigma$ | EXIT | Close position |

---

## Notebook vs Dashboard — Two Complementary Approaches

This project is split into two distinct layers that serve different purposes
and use data differently.

### Research Notebook (`iota_trading_strategy.ipynb`)

The notebook is the **full research pipeline** : it documents every methodological
choice, assumption, and limitation in detail. It is designed to be read like a
quantitative research paper.

**What it covers:**
- Raw data fetching, cleaning and anomaly detection (525 aberrant observations
  identified and removed from the ECB real yield series over 2021–2023)
- Step-by-step construction of the breakeven, swap proxy and IOTA
- Stationarity analysis and regime identification (4 distinct macro regimes
  identified over 2004–2025)
- Full parameter optimization across 27 configurations (window × entry × exit)
- Regime-by-regime P&L attribution
- Full diagnostic dashboard: rolling Sharpe, P&L distribution,
  z-score vs next-day P&L scatter (R² = 0.000)
- Critical analysis of model limitations

**Data used:** full historical series 2004–2025, static, loaded once.

### Interactive Dashboard (`dashboard/inflation-dashboard.py`)

The dashboard is a **live monitoring and simulation tool** — it fetches fresh
data from the ECB API at each session (cached for 1 hour) and focuses on
actionability rather than research depth.

**What it covers:**
- **Live Monitor:** current breakeven, IOTA level, z-score and active signal
  updated with latest ECB data
- **Backtest tab:** fully interactive — the user can adjust the rolling window
  (60–504 days), entry threshold (1–3σ) and exit band (0–1σ) and see the
  P&L and drawdown recompute in real time
- **Stress Test tab:** scenario analysis — simulates the impact of a ±100 bps
  breakeven shock on the IOTA level, z-score and signal across 11 shock scenarios

**Data used:** live ECB API calls, refreshed every session.

**Key difference:** the notebook uses cleaned, anomaly-filtered data with
documented methodological choices. The dashboard uses raw interpolated data
for real-time responsiveness — a deliberate trade-off between research
rigour and operational usability.


## Results

| Metric | Value |
|---|---|
| Period | 2005 – 2025 |
| Best Sharpe (optimized) | 0.15 |
| Total P&L | +8 bps/year |
| Max Drawdown | -420 bps |
| Nb Trades | 29 |

The strategy is **regime-dependent**: it performs well during smooth
mean-reversion environments (2010–2019, post-2023) but suffers during
acute stress episodes (GFC 2008, COVID 2020) where the basis diverges
persistently before snapping back.

> The Sharpe of 0.15 reflects the fundamental constraint of this study:
> the unavailability of public ZC swap quotes. With real-time swap rates
> (Bloomberg/Tullett), the signal would be sharper and the basis more
> precisely measured. This model is best interpreted as a **directional
> framework** rather than a production trading strategy.

## ZCIS Curve Notebook (`zc-inflation-swap-model.ipynb`)

Focuses on a more complex **curve construction** model from CPI projections:
- seasonal decomposition and forward CPI path
- annualized ZCIS proxy curve
- term‑structure diagnostics and limitations

**Data used:** HICP NSA monthly series.


## Getting Started

```bash
git clone https://github.com/mb69-code/inflation-trading
cd inflation-trading
pip install -r requirements.txt

# Run the dashboard locally
streamlit run dashboard/inflation-dashboard.py

# Or explore the full research notebook
jupyter notebook notebooks/01_data_construction.ipynb
```

---

## References

- Kerkhof, J. (2005). *Inflation Derivatives Explained*. Lehman Brothers Fixed Income. (https://the.earth.li/~jon/junk/kerkhof.pdf)
- Schulz, A. & Stapf, J. (2009). *Price discovery on traded inflation expectations*. BIS.
- ECB Statistical Data Warehouse — data-api.ecb.europa.eu
- Barclays Paper : *Global Inflation‑Linked Products: A User’s Guide*  
- Wanningen, C.F.A.R. (2007) : *Inflation Derivatives*, Blue Sky Group (Thesis)
  
