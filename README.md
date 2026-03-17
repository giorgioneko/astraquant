# AstraQuant — AI Auto-Investment Bot 📈🤖

AstraQuant is a sophisticated AI-powered trading bot with a beautiful dark-mode dashboard. It analyzes financial news sentiment and price data to make automated paper trading decisions across stocks, crypto, and ETFs.

## ✨ Features

- **AI Sentiment Analysis** — Plugs into any LLM (Local FinBERT, GPT-4o, Ollama, Claude, DeepSeek, Groq, and more via OpenAI-compatible API)
- **Live Market Data** — Tracks real-time prices for any stock, crypto, or ETF via Yahoo Finance
- **Dynamic Watchlist** — Add or remove any ticker symbol directly from the dashboard
- **Price Prediction** — Gradient Boosting ML model for price direction prediction
- **Paper Trading** — Safe simulation mode before going live
- **Historical Backtesting** — Validate the strategy against years of historical data
- **Premium Dashboard** — Beautiful glassmorphic dark-mode UI with real-time updates
- **Desktop App** — Runs as a standalone native window (PyQt6) or in your browser
- **Universal LLM Support** — Configure any OpenAI-compatible endpoint (local or cloud)

## 🖥️ Screenshots

| Dashboard | Settings |
|---|---|
| Portfolio value, live asset prices, trade logs | Manage watchlist tickers and AI engine |

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/astraquant.git
cd astraquant
```

### 2. Create a virtual environment and install dependencies
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Launch the app

**Option A — Double-click launcher (Windows):**  
Double-click `AstraQuant.vbs` for a seamless native window experience.

**Option B — Desktop App (terminal):**
```powershell
.\venv\Scripts\python.exe desktop_app.py
```

**Option C — Web Dashboard only (browser):**
```powershell
.\venv\Scripts\python.exe -m uvicorn api:app --reload
# Then open http://localhost:8000
```

**Option D — Terminal bot only:**
```powershell
.\venv\Scripts\python.exe main.py
```

## ⚙️ Configuration

All configuration is done through the **Settings** tab in the dashboard:

- **Watchlist** — Add any ticker (e.g. `TSLA`, `BTC-USD`, `NVDA`)
- **LLM Provider** — Choose your AI brain:
  - `Local FinBERT` — Free, offline, no API key needed
  - `OpenAI GPT-4o` — Best quality, requires API key
  - `Ollama / LMStudio` — Free local LLM server (e.g. `http://localhost:11434/v1`)
  - Any other OpenAI-compatible provider (Groq, DeepSeek, etc.)

### Optional: API Keys (`.env` file)
```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
```

## 🏗️ Project Structure

```
astraquant/
├── api.py                  # FastAPI backend (REST endpoints)
├── main.py                 # Core trading bot loop
├── desktop_app.py          # PyQt6 native window launcher
├── AstraQuant.vbs          # Silent double-click launcher
├── Launch_AstraQuant.bat   # Launcher (with terminal visible)
├── requirements.txt        # Python dependencies
├── data/
│   ├── database.py         # SQLite: prices, trades, settings, watchlist
│   ├── market_data.py      # Yahoo Finance & CCXT data fetcher
│   └── news_scraper.py     # Financial news headline fetcher
├── models/
│   ├── sentiment.py        # Universal LLM sentiment analyzer
│   └── price_predictor.py  # Gradient Boosting ML price predictor
├── trading/
│   ├── backtest.py         # Historical strategy backtester
│   ├── broker_client.py    # Paper trading execution client
│   └── risk_manager.py     # Position sizing & stop-loss rules
└── static/
    ├── index.html          # Dashboard UI
    ├── styles.css          # Glassmorphic dark-mode styles
    └── app.js              # Frontend logic & API calls
```

## ⚠️ Disclaimer

This software is for **educational and paper trading purposes only**. It is **not** financial advice. Always do your own research before investing real money. Past performance does not guarantee future results.

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
