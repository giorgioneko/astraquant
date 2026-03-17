import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

class PricePredictor:
    def __init__(self):
        # Using scikit-learn's GradientBoostingClassifier as our initial ML model
        # Note: XGBoost is often better but scikit-learn is already in our requirements
        self.model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False

    def prepare_features(self, df: pd.DataFrame):
        """
        Creates technical indicators to use as features for the ML model.
        """
        # Create a copy to avoid SettingWithCopyWarning
        data = df.copy()
        
        # Simple Moving Averages
        data['SMA_10'] = data['Close'].rolling(window=10).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        # Momentum (Rate of Change)
        data['ROC'] = data['Close'].pct_change(periods=5)
        
        # Volatility (Rolling Std Dev)
        data['Volatility'] = data['Close'].rolling(window=20).std()
        
        # Target variable: 1 if the next day's close is higher than today's, else 0
        data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
        
        # Drop NaN values created by rolling windows and shift
        data.dropna(inplace=True)
        return data

    def train(self, df: pd.DataFrame):
        """
        Trains the model on historical price data.
        """
        if len(df) < 100:
            print("Not enough data to train model. Need at least 100 periods.")
            return

        data = self.prepare_features(df)
        
        features = ['SMA_10', 'SMA_50', 'ROC', 'Volatility']
        X = data[features]
        y = data['Target']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        print("Training ML model on historical data...")
        self.model.fit(X_scaled, y)
        self.is_trained = True
        print(f"Model trained. Accuracy on training set: {self.model.score(X_scaled, y):.2f}")

    def predict(self, current_data: pd.DataFrame) -> dict:
        """
        Predicts whether the asset will go up (1) or down (0).
        """
        if not self.is_trained:
            print("Model is not trained yet. Defaulting to HOLD.")
            return {"action": "HOLD", "confidence": 0.0}
            
        # We need enough historical data to compute the features for the latest day
        if len(current_data) < 50:
            print("Not enough recent data to generate prediction.")
            return {"action": "HOLD", "confidence": 0.0}
            
        data = self.prepare_features(current_data)
        
        if len(data) == 0:
            return {"action": "HOLD", "confidence": 0.0}
            
        # Get the latest row's features
        latest_features = data[['SMA_10', 'SMA_50', 'ROC', 'Volatility']].iloc[-1:]
        
        # Scale current features
        latest_scaled = self.scaler.transform(latest_features)
        
        # Predict probability
        prob = self.model.predict_proba(latest_scaled)[0]
        
        # Prob[1] is the probability of class 1 (Up)
        prob_up = prob[1]
        
        if prob_up > 0.60:
            return {"action": "BUY", "confidence": prob_up}
        elif prob_up < 0.40:
            return {"action": "SELL", "confidence": 1 - prob_up}
        else:
            return {"action": "HOLD", "confidence": prob_up}
