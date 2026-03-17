import yfinance as yf
import pandas as pd
import datetime

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

if __name__ == "__main__":
    fetcher = MarketDataFetcher()
    data = fetcher.fetch_historical_stock_data("AAPL", period="1mo", interval="1d")
    print(data.head())
