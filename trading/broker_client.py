import os
from dotenv import load_dotenv

load_dotenv()

class BrokerClient:
    def __init__(self):
        # Placeholder for actual Alpaca/Binance API initialization
        self.api_key = os.getenv("BROKER_API_KEY")
        self.secret_key = os.getenv("BROKER_SECRET_KEY")
        self.is_paper = True
        
        # Mock portfolio state
        self.cash_balance = 100000.0
        self.positions = {}

    def get_account_balance(self) -> float:
        """Returns current cash balance."""
        print("[Broker] Fetching account balance...")
        return self.cash_balance

    def get_position(self, ticker: str) -> dict:
        """Returns details about current position in a ticker."""
        return self.positions.get(ticker, {"quantity": 0, "avg_price": 0.0})

    def execute_trade(self, action: str, ticker: str, quantity: float, price: float) -> bool:
        """
        Executes a paper trade.
        action: 'BUY' or 'SELL'
        """
        if action == "BUY":
            cost = quantity * price
            if self.cash_balance >= cost:
                self.cash_balance -= cost
                
                # Update position
                current_pos = self.get_position(ticker)
                new_qty = current_pos["quantity"] + quantity
                # Simplified average price approx
                new_avg = ((current_pos["quantity"] * current_pos["avg_price"]) + cost) / new_qty if new_qty > 0 else 0
                
                self.positions[ticker] = {"quantity": new_qty, "avg_price": new_avg}
                print(f"[Broker] EXECUTED BUY: {quantity} {ticker} @ ${price:.2f}. Remaining Cash: ${self.cash_balance:.2f}")
                return True
            else:
                print(f"[Broker] INSUFFICIENT FUNDS. Needed ${cost:.2f}, have ${self.cash_balance:.2f}")
                return False
                
        elif action == "SELL":
            current_pos = self.get_position(ticker)
            if current_pos["quantity"] >= quantity:
                revenue = quantity * price
                self.cash_balance += revenue
                
                # Update position
                new_qty = current_pos["quantity"] - quantity
                if new_qty == 0:
                    del self.positions[ticker]
                else:
                    self.positions[ticker]["quantity"] = new_qty
                    
                print(f"[Broker] EXECUTED SELL: {quantity} {ticker} @ ${price:.2f}. Remaining Cash: ${self.cash_balance:.2f}")
                return True
            else:
                print(f"[Broker] INVALID SELL. Don't own {quantity} of {ticker}.")
                return False
        return False
