import os
import sqlite3
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data.database import DatabaseManager

app = FastAPI(title="AI Trading Bot Dashboard")

# Initialize DB schema so settings tables exist on boot
_db_init = DatabaseManager()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mocked state for the API (in a real app, this would be tied to real broker objects)
bot_state = {
    "is_running": False,
    "cash_balance": 100000.0,
    "positions": {
        "AAPL": {"quantity": 50, "avg_price": 175.50},
        "MSFT": {"quantity": 20, "avg_price": 330.20}
    }
}

DB_PATH = "c:/Sources/Investing/trading_bot.db"

def get_db_connection():
    if not os.path.exists(DB_PATH):
        # Create an empty db file if it doesn't exist yet so API doesn't crash on empty starts
        conn = sqlite3.connect(DB_PATH)
        conn.close()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/portfolio")
def get_portfolio():
    return {
        "balance": bot_state["cash_balance"],
        "positions": bot_state["positions"]
    }

@app.get("/api/logs")
def get_recent_logs(limit: int = 50):
    try:
        conn = get_db_connection()
        logs = conn.execute("SELECT * FROM trade_log ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [dict(ix) for ix in logs]
    except sqlite3.OperationalError:
        # Table might not exist yet if bot hasn't run
        return []

@app.get("/api/bot/status")
def get_bot_status():
    return {"status": "Running" if bot_state["is_running"] else "Stopped"}

@app.post("/api/bot/toggle")
def toggle_bot():
    bot_state["is_running"] = not bot_state["is_running"]
    return {"status": "Running" if bot_state["is_running"] else "Stopped"}

@app.get("/api/market-data")
def get_market_data():
    """Fetch latest price data from yfinance for all watchlist tickers."""
    try:
        import yfinance as yf
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ticker FROM watchlist WHERE active=1")
        tickers = [row['ticker'] for row in cursor.fetchall()]
        conn.close()

        if not tickers:
            return []

        results = []
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).fast_info
                results.append({
                    "ticker": ticker,
                    "price": round(float(info.last_price), 2) if info.last_price else None,
                    "change_pct": round(float(
                        (info.last_price - info.previous_close) / info.previous_close * 100
                    ), 2) if info.last_price and info.previous_close else None,
                })
            except Exception as e:
                results.append({"ticker": ticker, "price": None, "change_pct": None})

        return results
    except Exception as e:
        return []

# Trending tickers — mix of popular stocks and crypto
TRENDING_TICKERS = [
    "NVDA", "TSLA", "AAPL", "MSFT", "META", "GOOGL", "AMZN",
    "BTC-USD", "ETH-USD", "SOL-USD",
    "SPY", "QQQ"
]

@app.get("/api/trending")
def get_trending():
    """Returns 7-day price history + current stats for trending tickers."""
    try:
        import yfinance as yf
        results = []
        for ticker in TRENDING_TICKERS:
            try:
                tk = yf.Ticker(ticker)
                hist = tk.history(period="7d", interval="1h")
                fast = tk.fast_info

                prices = [round(float(p), 2) for p in hist["Close"].dropna().tolist()]
                timestamps = [str(ts) for ts in hist.index.strftime("%Y-%m-%dT%H:%M").tolist()]

                current = round(float(fast.last_price), 2) if fast.last_price else None
                prev = round(float(fast.previous_close), 2) if fast.previous_close else None
                change_pct = round((current - prev) / prev * 100, 2) if current and prev else None

                results.append({
                    "ticker": ticker,
                    "price": current,
                    "change_pct": change_pct,
                    "prices": prices[-48:],         # last 48 hourly points  (~2 days visual)
                    "timestamps": timestamps[-48:],
                })
            except Exception as e:
                results.append({"ticker": ticker, "price": None, "change_pct": None, "prices": [], "timestamps": []})
        return results
    except Exception as e:
        return []

# --- New Configuration Endpoints ---

@app.get("/api/settings")
def get_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    conn.close()
    return settings

class SettingsUpdate(BaseModel):
    llm_provider: str
    llm_base_url: str
    llm_model: str
    llm_api_key: str

@app.post("/api/settings")
def update_settings(updates: SettingsUpdate):
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("llm_provider", updates.llm_provider))
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("llm_base_url", updates.llm_base_url))
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("llm_model", updates.llm_model))
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("llm_api_key", updates.llm_api_key))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/watchlist")
def get_watchlist():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker FROM watchlist WHERE active=1")
    tickers = [row['ticker'] for row in cursor.fetchall()]
    conn.close()
    return {"tickers": tickers}

class WatchlistUpdate(BaseModel):
    ticker: str

@app.post("/api/watchlist")
def add_to_watchlist(item: WatchlistUpdate):
    conn = get_db_connection()
    
    # Simple validation for a capitalized ticker (max 10 chars, letters only approx)
    clean_ticker = item.ticker.strip().upper()
    if len(clean_ticker) > 0 and len(clean_ticker) <= 10:
        conn.execute("INSERT OR REPLACE INTO watchlist (ticker, active) VALUES (?, 1)", (clean_ticker,))
        conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/watchlist/{ticker}")
def remove_from_watchlist(ticker: str):
    conn = get_db_connection()
    conn.execute("DELETE FROM watchlist WHERE ticker=?", (ticker.strip().upper(),))
    conn.commit()
    conn.close()
    return {"status": "success"}

# Ensure the static directory exists before mounting
os.makedirs("c:/Sources/Investing/static", exist_ok=True)
app.mount("/", StaticFiles(directory="c:/Sources/Investing/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Make sure we run from the correct directory so static mounts work
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
