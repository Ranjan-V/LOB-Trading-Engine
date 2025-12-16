# Limit Order Book Trading Engine

Quantitative trading simulation engine with market making strategies and backtesting framework.

## Features
- Real-time limit order book simulation
- Market making strategy with inventory management
- High-frequency data backtesting
- Performance analytics (Sharpe ratio, max drawdown, PnL)
- Interactive web dashboard

## Tech Stack
Python, NumPy, Pandas, Flask, Plotly, Binance API

# Quantitative Market Simulation Engine

A high-performance Limit Order Book (LOB) exchange simulator and Market Making bot built in Python. The system simulates a realistic trading environment with price-time priority matching, network latency, and slippage to test quantitative strategies on real historical data.

## 📊 Backtest Performance (Live Results)
The strategy was stress-tested on **10,080 real Bitcoin (BTC) market data points** (1-minute candles) over a 7-day period.

> **Market Context:** During the testing period, the price of Bitcoin **dropped by 4.5%**. Despite this downtrend, the Market Making strategy generated a positive return, demonstrating uncorrelated alpha.

| Metric | Result | Notes |
| :--- | :--- | :--- |
| **Total Return** | `+5.41%` | Approx. **1,460%** Annualized |
| **Win Rate** | `80.8%` | High probability of successful quoting |
| **Profit Factor** | `2.15` | Gross Profit / Gross Loss |
| **Max Drawdown** | `2.86%` | Strictly controlled via inventory risk management |
| **Total Trades** | `1,611` | High-frequency execution speed |
| **Latency** | `<1ms` | Internal matching engine processing time |

---

## 🏗 System Architecture

The project is architected into four modular components, designed to mimic a production trading stack:

### ✅ Module 1: Data Collection
* **Real-time Fetcher:** Connects to Binance API to retrieve live market data.
* **Data Processor:** Validates integrity and processes 10,000+ rows of historical candle data.
* **Storage:** Efficient management of time-series data for backtesting.

### ✅ Module 2: Order Book Engine (Core)
* **Matching Logic:** Implements **Price-Time Priority** matching (standard exchange protocol).
* **Simulation:** Features a poisson-process order flow simulator to mimic organic market activity.
* **Realism:** Models execution latency and slippage to prevent unrealistic backtest results.

### ✅ Module 3: Market Making Strategy
* **Inventory Management:** Dynamic skewing of bid/ask prices based on current inventory held to minimize directional risk.
* **PnL Tracking:** Real-time calculation of realized vs. unrealized PnL.
* **Risk Controls:** Auto-halts trading if drawdown limits are breached.

### ✅ Module 4: Backtesting & Analytics
* **Framework:** Replays historical data tick-by-tick against the matching engine.
* **Analytics:** Calculates institutional-grade metrics (Sharpe Ratio, VaR, Sortino Ratio).
* **Visualization:** Interactive dashboards using **Plotly** to visualize Order Book Depth, Trade Flow, and Equity Curves.

## 🛠 Tech Stack
* **Core:** Python, NumPy, Pandas
* **Visualization:** Plotly, Matplotlib
* **Web/Dashboard:** Flask
* **Data Source:** Binance Public API

## Author
Ranjan V - Aspiring Quantitative Developer

## Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```