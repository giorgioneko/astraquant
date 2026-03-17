import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from data.market_data import MarketDataFetcher
from models.price_predictor import PricePredictor
from trading.risk_manager import RiskManager

def run_backtest(ticker: str, start_date: str, end_date: str):
    print(f"--- Starting backtest for {ticker} from {start_date} to {end_date} ---")
    fetcher = MarketDataFetcher()
    predictor = PricePredictor()
    risk_manager = RiskManager()
    
    # Fetch historical data
    df = fetcher.fetch_historical_stock_data(ticker, period="5y", interval="1d")
    if df.empty:
        print("No data fetched.")
        return
        
    df = df.loc[start_date:end_date]
    if len(df) < 100:
        print("Not enough data for backtest simulation.")
        return
        
    # Split into train/test
    train_size = int(len(df) * 0.5)
    train_data = df.iloc[:train_size]
    test_data = df.iloc[train_size:]
    
    print("\nTraining model on first half of historical data...")
    predictor.train(train_data)
    
    cash = 100000.0
    initial_cash = cash
    position = 0
    entry_price = 0.0
    
    print("\nRunning simulation over test data...")
    for i in range(50, len(test_data)):
        current_date_data = test_data.iloc[:i]
        latest_row = current_date_data.iloc[-1]
        current_price = latest_row['Close']
        date = current_date_data.index[-1]
        
        # Check exit conditions
        if position > 0:
            exit_action = risk_manager.check_exit_conditions(entry_price, current_price)
            if exit_action != "HOLD":
                cash += position * current_price
                print(f"[{date.date()}] {exit_action} at {current_price:.2f}. PnL: {(current_price - entry_price)/entry_price:.2%} | Remaining Cash: ${cash:.2f}")
                position = 0
                entry_price = 0.0
                continue
                
        # Make prediction
        pred = predictor.predict(current_date_data)
        
        # We simplify sentiment to 0.5 for backtesting since historical news is hard to fetch freely
        overall_conviction = (pred['confidence'] + 0.5) / 2
        
        if pred['action'] == "BUY" and position == 0 and overall_conviction > 0.6:
            qty = risk_manager.calculate_position_size(cash, current_price, overall_conviction)
            if qty > 0:
                cost = qty * current_price
                if cash >= cost:
                    cash -= cost
                    position += qty
                    entry_price = current_price
                    print(f"[{date.date()}] BUY {qty} shares at {current_price:.2f} | Conviction: {overall_conviction:.2f}")
                    
    final_value = cash + (position * test_data.iloc[-1]['Close'])
    buy_and_hold_return = (test_data.iloc[-1]['Close'] - test_data.iloc[50]['Close']) / test_data.iloc[50]['Close']
    
    print(f"\n--- Backtest Results for {ticker} ---")
    print(f"Initial Capital: ${initial_cash:.2f}")
    print(f"Final Capital:   ${final_value:.2f}")
    print(f"Total Return:    {((final_value - initial_cash)/initial_cash):.2%}")
    print(f"Buy & Hold Ret:  {buy_and_hold_return:.2%}")
    print("--------------------------------------\n")
    
from data.database import DatabaseManager

if __name__ == "__main__":
    db = DatabaseManager()
    tickers = db.get_watchlist()
    
    if not tickers:
        print("Watchlist empty, defaulting to AAPL.")
        tickers = ["AAPL"]
         
    for t in tickers:
        run_backtest(t, "2020-01-01", "2025-12-31")
