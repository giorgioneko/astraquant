import yfinance as yf
import pandas as pd
import datetime
import sys

TRENDING_TICKERS = [
    "NVDA", "TSLA", "AAPL", "MSFT", "META", "GOOGL", "AMZN",
    "BTC-USD", "ETH-USD", "SOL-USD",
    "SPY", "QQQ"
]

class MarketDataFetcher:
    def __init__(self):
        pass
        
    def fetch_historical_stock_data(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        Fetches historical data for a specific stock ticker using yfinance.
        """
        print(f"Fetching {period} of {interval} data for {ticker}...")
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        return df

    def get_ascii_sparkline(self, prices):
        """Generates a small ASCII sparkline for terminal output."""
        if not prices or len(prices) < 2: return "[No Data]"
        
        # Try Unicode block characters first
        chars = ' ▂▃▄▅▆▇█'
        min_p, max_p = min(prices), max(prices)
        if max_p == min_p: return '▄' * len(prices)
        
        try:
            sparkline = "".join(
                chars[int((p - min_p) / (max_p - min_p) * 7)]
                for p in prices
            )
            # Test if current stdout can handle it
            sparkline.encode(sys.stdout.encoding or 'ascii')
            return sparkline
        except (UnicodeEncodeError, TypeError):
            # Fallback to very basic ASCII if terminal is old/picky
            ascii_chars = '_.-^'
            return "".join(
                ascii_chars[int((p - min_p) / (max_p - min_p) * 3)]
                for p in prices
            )

    def fetch_trending_markets(self):
        """Fetches 7-day price history + current stats for trending tickers."""
        results = []
        for ticker in TRENDING_TICKERS:
            try:
                tk = yf.Ticker(ticker)
                hist = tk.history(period="7d", interval="1h")
                fast = tk.fast_info

                prices = [round(float(p), 2) for p in hist["Close"].dropna().tolist()]
                timestamps = [str(ts) for ts in hist.index.strftime("%Y-%m-%dT%H:%M").tolist()]
                
                # Take last 24 hourly points for the sparkline
                sparkline_data = prices[-24:]
                
                current = round(float(fast.last_price), 2) if fast.last_price else None
                prev = round(float(fast.previous_close), 2) if fast.previous_close else None
                change_pct = round((current - prev) / prev * 100, 2) if current and prev else None

                results.append({
                    "ticker": ticker,
                    "price": current,
                    "change_pct": change_pct,
                    "prices": prices[-48:], # Keep more for web UI
                    "timestamps": timestamps[-48:],
                    "sparkline": self.get_ascii_sparkline(sparkline_data)
                })
            except Exception:
                results.append({
                    "ticker": ticker, "price": None, "change_pct": None, 
                    "prices": [], "sparkline": "[No Data]"
                })
        return results

if __name__ == "__main__":
    fetcher = MarketDataFetcher()
    trending = fetcher.fetch_trending_markets()
    for t in trending:
        print(f"{t['ticker']}: ${t['price']} ({t['change_pct']}%) {t['sparkline']}")
