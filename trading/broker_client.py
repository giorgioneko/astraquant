import os
import requests
from dotenv import load_dotenv
from data.database import DatabaseManager

load_dotenv()

class BrokerClient:
    def __init__(self):
        self.db = DatabaseManager()
        self.broker_type = self.db.get_setting("broker_type") or "mock"
        
        self.api_key = self.db.get_setting("broker_api_key") or os.getenv("BROKER_API_KEY")
        self.secret_key = self.db.get_setting("broker_secret_key") or os.getenv("BROKER_SECRET_KEY")
        self.base_url = self.db.get_setting("broker_base_url") or "https://paper-api.alpaca.markets"
        self.is_paper = True
        
        # Headers for actual Alpaca API initialization
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        } if self.api_key and self.secret_key else {}
        
        # Mock portfolio state
        self.cash_balance = 100000.0
        self.positions = {}

    def get_account_balance(self) -> float:
        """Returns current cash balance."""
        if self.broker_type == "external" and self.api_key and self.secret_key and "alpaca" in self.base_url:
            try:
                res = requests.get(f"{self.base_url}/v2/account", headers=self.headers)
                if res.status_code == 200:
                    return float(res.json().get("cash", 0.0))
            except Exception as e:
                print(f"[Broker] Alpaca connection error: {e}")

        print("[Broker] Fetching mock account balance...")
        return self.cash_balance

    def get_position(self, ticker: str) -> dict:
        """Returns details about current position in a ticker."""
        if self.broker_type == "external" and self.api_key and self.secret_key and "alpaca" in self.base_url:
            try:
                res = requests.get(f"{self.base_url}/v2/positions/{ticker}", headers=self.headers)
                if res.status_code == 200:
                    data = res.json()
                    return {"quantity": float(data.get("qty", 0)), "avg_price": float(data.get("avg_entry_price", 0))}
                else:
                    return {"quantity": 0, "avg_price": 0.0}
            except Exception as e:
                print(f"[Broker] Alpaca position error: {e}")

        return self.positions.get(ticker, {"quantity": 0, "avg_price": 0.0})

    def execute_trade(self, action: str, ticker: str, quantity: float, price: float) -> bool:
        """
        Executes a paper trade.
        action: 'BUY' or 'SELL'
        """
        print(f"[Broker] Preparing to {action} {quantity} {ticker}...")
        
        if self.broker_type == "external" and self.api_key and self.secret_key:
            # Currently only Alpaca-like REST logic is fully matched:
            if "alpaca" in self.base_url:
                try:
                    side = "buy" if action == "BUY" else "sell"
                    payload = {
                        "symbol": ticker,
                        "qty": str(quantity),
                        "side": side,
                        "type": "market",
                        "time_in_force": "day"
                    }
                    res = requests.post(f"{self.base_url}/v2/orders", headers=self.headers, json=payload)
                    if res.status_code in [200, 201]:
                        print(f"[Broker] EXTERNAL {action} SUCCESS: {quantity} {ticker}.")
                        return True
                    else:
                        print(f"[Broker] EXTERNAL {action} FAILED: {res.text}")
                        return False
                except Exception as e:
                    print(f"[Broker] External trade error: {e}")
                    return False

        # Fallback to Mock trade execution
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
