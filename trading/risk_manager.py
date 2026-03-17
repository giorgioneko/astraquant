class RiskManager:
    def __init__(self, max_risk_per_trade_pct: float = 0.02, stop_loss_pct: float = 0.05, take_profit_pct: float = 0.10):
        # By default, risk max 2% of portfolio per trade
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def calculate_position_size(self, account_balance: float, current_price: float, confidence: float) -> float:
        """
        Determines how many shares/coins to buy based on account balance and risk limits.
        Higher confidence can marginally increase position size within risk limits.
        """
        if current_price <= 0:
            return 0.0
            
        # Max dollar amount we're willing to risk on this trade
        max_risk_dollars = account_balance * self.max_risk_per_trade_pct
        
        # Adjust risk by model confidence (e.g. 0.6 confidence means we take 60% of our max allowed risk)
        # Assuming minimum confidence to trade is 0.5 (random guess)
        adjusted_risk = max_risk_dollars * ((confidence - 0.5) * 2) if confidence > 0.5 else 0
        
        # Ensure we don't exceed max risk
        final_risk_dollars = min(adjusted_risk, max_risk_dollars)
        
        # To determine position size, we assume we get stopped out at stop_loss_pct
        # Risk = Position Size * (Entry Price - Stop Loss Price)
        # Position Size = Risk / (Entry Price * Stop Loss Pct)
        
        loss_per_share = current_price * self.stop_loss_pct
        
        if loss_per_share == 0:
            return 0.0
            
        num_shares = final_risk_dollars / loss_per_share
        
        # Return an integer amount of shares for simplicity in stocks, though crypto can be fractional
        return max(0.0, float(int(num_shares)))

    def check_exit_conditions(self, entry_price: float, current_price: float) -> str:
        """
        Checks if we hit stop loss or take profit. Returns action or 'HOLD'.
        """
        if entry_price <= 0:
            return "HOLD"
            
        pct_change = (current_price - entry_price) / entry_price
        
        if pct_change <= -self.stop_loss_pct:
            return "SELL_STOP_LOSS"
        elif pct_change >= self.take_profit_pct:
            return "SELL_TAKE_PROFIT"
        else:
            return "HOLD"
