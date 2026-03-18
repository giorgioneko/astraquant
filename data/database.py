import sqlite3
import os
import pandas as pd
from datetime import datetime

# Resolve DB path relative to this file's parent directory (project root)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "trading_bot.db")

class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or _DEFAULT_DB_PATH
        self._init_db()

    def _init_db(self):
        """Creates the necessary tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for storing daily price data to avoid hitting APIs unnecessarily
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_prices (
            ticker TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (ticker, date)
        )
        ''')
        
        # Table for logging executed trades
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ticker TEXT,
            action TEXT,
            price REAL,
            quantity REAL,
            sentiment_score REAL,
            model_confidence REAL
        )
        ''')
        
        # Table for app settings (like LLM Base URL, Model Name, API Key)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')

        # Default settings if none exist
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('llm_provider', 'finbert')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('llm_base_url', 'https://api.openai.com/v1')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('llm_model', 'gpt-4o')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('llm_api_key', '')")

        # Table for Broker/Paper Trading settings
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('broker_type', 'mock')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('broker_api_key', '')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('broker_secret_key', '')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('broker_base_url', 'https://paper-api.alpaca.markets')")


        # Table for Dynamic Watchlist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            ticker TEXT PRIMARY KEY,
            active INTEGER DEFAULT 1
        )
        ''')
        
        # Table for MCP Servers
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mcp_servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            command TEXT NOT NULL,
            args TEXT,
            env_vars TEXT
        )
        ''')
        
        # Insert default tickers
        for t in ["AAPL", "MSFT", "GOOGL"]:
            cursor.execute("INSERT OR IGNORE INTO watchlist (ticker, active) VALUES (?, 1)", (t,))

        conn.commit()
        conn.close()

    def get_setting(self, key: str) -> str:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ""

    def update_setting(self, key: str, value: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    def get_watchlist(self) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ticker FROM watchlist WHERE active=1")
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]

    def add_to_watchlist(self, ticker: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT OR REPLACE INTO watchlist (ticker, active) VALUES (?, 1)", (ticker,))
        conn.commit()
        conn.close()

    def remove_from_watchlist(self, ticker: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM watchlist WHERE ticker=?", (ticker,))
        conn.commit()
        conn.close()

    def get_mcp_servers(self) -> list:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mcp_servers")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_mcp_server(self, name: str, command: str, args: str, env_vars: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO mcp_servers (name, command, args, env_vars) VALUES (?, ?, ?, ?)",
            (name, command, args, env_vars)
        )
        conn.commit()
        conn.close()

    def delete_mcp_server(self, server_id: int):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM mcp_servers WHERE id=?", (server_id,))
        conn.commit()
        conn.close()

    def save_daily_prices(self, ticker: str, df: pd.DataFrame):
        """Saves a pandas dataframe of daily prices to the database."""
        conn = sqlite3.connect(self.db_path)
        for index, row in df.iterrows():
            date_str = index.strftime('%Y-%m-%d')
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO daily_prices (ticker, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (ticker, date_str, row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))
            except Exception as e:
                print(f"Db insert error for {ticker} on {date_str}: {e}")
                
        conn.commit()
        conn.close()

    def log_trade(self, ticker: str, action: str, price: float, quantity: float, sentiment: float, confidence: float):
        """Logs an executed trade to the database."""
        conn = sqlite3.connect(self.db_path)
        timestamp = datetime.now().isoformat()
        conn.execute('''
            INSERT INTO trade_log (timestamp, ticker, action, price, quantity, sentiment_score, model_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, ticker, action, price, quantity, sentiment, confidence))
        conn.commit()
        conn.close()
