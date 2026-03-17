import time
from data.market_data import MarketDataFetcher
from data.news_scraper import NewsFetcher
from data.database import DatabaseManager
from models.sentiment import SentimentAnalyzer
from models.price_predictor import PricePredictor
from trading.broker_client import BrokerClient
from trading.risk_manager import RiskManager

def main():
    print("Starting AI Trading Bot...")
    
    # Initialize components
    db = DatabaseManager()
    market_fetcher = MarketDataFetcher()
    news_fetcher = NewsFetcher()
    
    sentiment_model = SentimentAnalyzer()
    predictor = PricePredictor()
    
    broker = BrokerClient()
    risk_manager = RiskManager()
    
    # Pre-train the model
    print("Pre-training ML model on historical data...")
    # Get initial watchlist to train on
    initial_tickers = db.get_watchlist()
    if not initial_tickers:
        initial_tickers = ["AAPL"]
        
    for ticker in initial_tickers:
        hist_data = market_fetcher.fetch_historical_stock_data(ticker, period="1y", interval="1d")
        if not hist_data.empty:
            db.save_daily_prices(ticker, hist_data)
            predictor.train(hist_data)
    
    while True:
        try:
            # 1. Fetch dynamic settings
            tickers_to_watch = db.get_watchlist()
            
            provider = db.get_setting('llm_provider')
            base_url = db.get_setting('llm_base_url')
            model_name = db.get_setting('llm_model')
            api_key = db.get_setting('llm_api_key')
            
            sentiment_model = SentimentAnalyzer(
                provider=provider,
                base_url=base_url if base_url else None,
                api_key=api_key if api_key else None,
                model=model_name if model_name else "gpt-4o"
            )
            
            print(f"\n--- New Cycle - Balance: ${broker.get_account_balance():.2f} ---")
            
            if not tickers_to_watch:
                print("Watchlist empty. Add tickers via the Dashboard Settings tab.")
                time.sleep(10)
                continue
                
            for ticker in tickers_to_watch:
                print(f"--- Processing {ticker} ---")
                
                # 1. Fetch Market Data for prediction
                df = market_fetcher.fetch_historical_stock_data(ticker, period="3mo", interval="1d")
                if df.empty:
                    continue
                db.save_daily_prices(ticker, df)
                
                current_price = df['Close'].iloc[-1]
                
                # Check for exit conditions first
                position = broker.get_position(ticker)
                if position["quantity"] > 0:
                    exit_action = risk_manager.check_exit_conditions(position["avg_price"], current_price)
                    if exit_action != "HOLD":
                        broker.execute_trade("SELL", ticker, position["quantity"], current_price)
                        db.log_trade(ticker, exit_action, current_price, position["quantity"], 0.0, 0.0)
                        continue # Move to next ticker if we sold

                # 2. Fetch News and Analyze Sentiment
                news_items = news_fetcher.fetch_recent_news(ticker, days_back=1)
                sentiment_score_avg = 0.5 # Neutral baseline
                
                if news_items:
                    total_score = 0
                    for item in news_items:
                        sentiment = sentiment_model.analyze_headline(item['title'])
                        
                        label = sentiment['label'].lower()
                        score = sentiment['score']
                        if 'positive' in label:
                            total_score += score
                        elif 'negative' in label:
                            total_score -= score
                    
                    # Approximate average sentiment (-1 to 1, shifted to 0 to 1 for simplicity)
                    valid_items = len(news_items)
                    avg = total_score / valid_items if valid_items > 0 else 0
                    sentiment_score_avg = (avg + 1) / 2
                    print(f"[{ticker}] Avg News Sentiment: {sentiment_score_avg:.2f}")

                # 3. Make Prediction
                prediction = predictor.predict(df)
                action = prediction["action"]
                confidence = prediction["confidence"]
                
                print(f"[{ticker}] Prediction: {action} (Confidence: {confidence:.2f})")
                
                # Combine ML confidence and Sentiment to adjust overall conviction
                overall_conviction = (confidence + sentiment_score_avg) / 2
                
                # 4. Execute Trade based on Risk Manager
                if action == "BUY" and overall_conviction > 0.6:
                    qty = risk_manager.calculate_position_size(
                        broker.get_account_balance(), 
                        current_price, 
                        overall_conviction
                    )
                    if qty > 0:
                        success = broker.execute_trade("BUY", ticker, qty, current_price)
                        if success:
                            db.log_trade(ticker, "BUY", current_price, qty, sentiment_score_avg, confidence)
                elif action == "SELL":
                    if position["quantity"] > 0:
                        qty_to_sell = position["quantity"]
                        success = broker.execute_trade("SELL", ticker, qty_to_sell, current_price)
                        if success:
                            db.log_trade(ticker, "SELL", current_price, qty_to_sell, sentiment_score_avg, confidence)

            print("Cycle complete. Waiting for next interval...")
            time.sleep(3600) # Sleep for an hour
            
        except KeyboardInterrupt:
            print("Bot stopped by user.")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
