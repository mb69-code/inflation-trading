# Inflation Trading — IOTA Monitor

> End-to-end inflation basis trading framework: data pipeline, signal generation, 
> backtesting, and interactive dashboard — built on live ECB data.

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
│   └── 01_data_construction.ipynb   # Full research pipeline
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

## Methodology

### Data sources (ECB Statistical Data Warehouse)
| Series | Dataflow | Description |
|---|---|---|
| Nominal 10Y | `YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y` | Euro area AAA govt bonds |
| Real 10Y | `FM/M.U2.EUR.4F.BB.R_U2_10Y.YLDA` | Inflation-linked benchmark |
| HICP YoY | `ICP/M.U2.N.000000.4.ANR` | Euro area realized inflation |

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

## Interactive Dashboard

A full Streamlit dashboard provides three views:

- **Live Monitor** — Real-time breakeven, IOTA level, z-score and active signal
- **Backtest** — Adjustable parameters (window, entry/exit thresholds), 
  cumulative P&L and drawdown
- **Stress Test** — Scenario analysis: impact of ±100 bps breakeven shock 
  on signal and position

```bash
pip install -r requirements.txt
streamlit run dashboard/inflation-dashboard.py
```

## Getting Started

```bash
git clone https://github.com/mb69-code/inflation-trading
cd inflation-trading
pip install -r requirements.txt

# Run the dashboard
streamlit run dashboard/inflation-dashboard.py

# Or explore the full research notebook
jupyter notebook notebooks/01_data_construction.ipynb
```

## References

- Kerkhof, J. (2005). *Inflation Derivatives Explained*. Lehman Brothers Fixed Income.
- Schulz, A. & Stapf, J. (2009). *Price discovery on traded inflation expectations*. BIS.
- ECB Statistical Data Warehouse — data-api.ecb.europa.eu
