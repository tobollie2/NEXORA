# 🧠 NEXORA – Quantitative Trading & Research Framework  
**Version:** Development Build (October 2025)  
**Environment:** Python 3.11 (venv: `test_env`)  
**Platform:** Local VS Code + Pylance  

---

## 1. 🧭 Project Overview

**NEXORA** is a modular, research-grade trading and backtesting framework designed for strategy development, performance analysis, and portfolio optimization.  
It integrates every stage of the algorithmic trading pipeline — from raw market data ingestion to multi-strategy backtesting and reporting.

### 🧩 Core System Architecture

| Layer | Description |
|-------|--------------|
| **/config** | Configuration and environment management (`settings.yaml`, loader) |
| **/data** | Ingestion, cleaning, and validation of Kraken market data |
| **/strategies** | Modular trading strategies (Trend Following, Mean Reversion, Stat Arb) |
| **/backtest** | Multi-strategy backtesting engine, metrics, HTML reports |
| **/portfolio** | Portfolio allocator and position tracking |
| **/risk** | Risk manager with drawdown and capital constraints |
| **/monitoring** | Logging utilities and diagnostic tools |
| **/tools** | Optimization, analytics, and cleanup utilities |

---

## 2. 🧱 Current Functional Components

### ✅ Core Modules (Stable)
- **`config/settings_loader.py`** → Loads YAML config and validates all system paths.  
- **`data/ingestion.py`** → Handles Kraken historical and simulated data feeds.  
- **`monitoring/logging_utils.py`** → Centralized logging for all modules.  
- **`portfolio/allocator.py`** → Capital allocation and position management.  
- **`risk/risk_manager.py`** → Evaluates drawdown, exposure, and risk state.  
- **`backtest/backtest_runner.py`** → Runs all strategies in parallel; outputs CSV + HTML reports.  
- **`backtest/report_generator.py`** → Creates visual, Plotly-based performance summaries.  
- **`tools/diagnostic_check.py`** → Validates environment integrity, data presence, and paths.  

---

## 3. 📊 Strategies Implemented

| Strategy | Type | Description | Status |
|-----------|------|--------------|--------|
| **TrendFollowingStrategy** | Momentum | SMA crossover (short vs. long) | ✅ Stable |
| **MeanReversionStrategy** | Contrarian | Bollinger band or Z-score mean reversion | ✅ Stable |
| **StatisticalArbitrageStrategy** | Pair-trading | Price ratio + Z-score between correlated pairs | ✅ Stable |

Each strategy supports:  
- Configurable parameter grid (for optimization).  
- Safe numeric casting and missing-data handling.  
- Backtest-compatible `.run_backtest()` function returning performance metrics.  

---

## 4. 💾 Data System

### Current State:
- Cleaned historical **Kraken** 1m OHLCV data for BTC, ETH, SOL, XRP, ADA.  
- Each file stored in `/data/cleaned/` as `SYMBOL_USD_1m_cleaned.csv`.  

### Planned:
- Expand to full historical data (multi-year).  
- Implement automatic incremental updates.  

---

## 5. 🔍 Backtesting Framework (v2)

The **`backtest_runner.py`** executes all active strategies in **parallel threads** using `ThreadPoolExecutor`.  
It supports:
- Multi-asset, multi-strategy execution.  
- Automated logging and result aggregation.  
- Summary CSV + interactive HTML report via `BacktestReportGenerator`.  

**Metrics Tracked:**
- Total Return  
- Drawdown  
- Sharpe Ratio *(to be extended)*  
- Volatility *(to be added)*  
- Trade Count *(to be added)*  

---

## 6. 🧮 Analytics & Reporting

### ✅ Current:
- CSV summaries of all strategy runs.  
- Plotly-powered interactive HTML reports.  

### 🚧 Upcoming Enhancements:
- Rolling 30-trade metrics:
  - Rolling Sharpe Ratio  
  - Rolling Volatility  
  - Rolling Max Drawdown  
- Portfolio equity curve visualization.  
- Comparison between strategies across assets.

---

## 7. ⚙️ Optimization Framework

**Module:** `optimization_runner.py`  
- Performs parameter sweeps using `ThreadPoolExecutor`.  
- Automatically loads `parameter_grid()` from each strategy.  
- Logs results to CSV and summarizes best configurations.  
- Future support for Bayesian and genetic optimization planned.  

---

## 8. 🔧 Environment & Dependencies

| Package | Purpose |
|----------|----------|
| `pandas` | Core data handling |
| `numpy` | Numerical computation |
| `plotly` | HTML report visualization |
| `pyyaml` | Config management |
| `requests` | Data fetching (Kraken API) |
| `concurrent.futures` | Parallel execution |
| `rich` | Console formatting (legacy monitoring) |
| `matplotlib` | Optional plots in diagnostics |
| `logging` | Unified logging infrastructure |

All dependencies installed inside:
