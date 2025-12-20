#!/usr/bin/env python3
"""
Example script demonstrating basic usage of AlphaGenesis.

This script shows how to:
1. Fetch market data
2. Engineer features
3. Train a model
4. Run a backtest
"""

import pandas as pd
from datetime import datetime, timedelta

from alphagenesis.data import WEEXClient, DataFetcher
from alphagenesis.features import FeatureEngineer
from alphagenesis.models import LSTMModel
from alphagenesis.backtest import Backtester, PerformanceMetrics
from alphagenesis.risk import RiskManager
from alphagenesis.utils import setup_logger, Config

# Setup
setup_logger(log_level="INFO")
config = Config("config/config.yaml")

print("=" * 60)
print("AlphaGenesis - Example Usage")
print("=" * 60)

# 1. Fetch Market Data
print("\n1. Fetching market data...")
weex_client = WEEXClient()
data_fetcher = DataFetcher(weex_client)

symbol = "BTC/USDT"
try:
    df = data_fetcher.fetch_ohlcv(symbol, interval="1h")
    print(f"   Fetched {len(df)} candlesticks for {symbol}")
except Exception as e:
    print(f"   Note: Using sample data (API not configured: {e})")
    # Create sample data for demonstration
    dates = pd.date_range(end=datetime.now(), periods=1000, freq="1H")
    df = pd.DataFrame({
        "timestamp": dates,
        "open": 50000 + (pd.Series(range(1000)) * 10) + (pd.Series(range(1000)).apply(lambda x: x % 100)),
        "high": 50100 + (pd.Series(range(1000)) * 10) + (pd.Series(range(1000)).apply(lambda x: x % 100)),
        "low": 49900 + (pd.Series(range(1000)) * 10) + (pd.Series(range(1000)).apply(lambda x: x % 100)),
        "close": 50000 + (pd.Series(range(1000)) * 10) + (pd.Series(range(1000)).apply(lambda x: x % 100)),
        "volume": 1000 + (pd.Series(range(1000)) * 5),
    })
    df.set_index("timestamp", inplace=True)

# 2. Feature Engineering
print("\n2. Engineering features...")
feature_engineer = FeatureEngineer()
df_with_features = feature_engineer.create_features(df)
print(f"   Created {len(df_with_features.columns)} features")

# 3. Risk Assessment
print("\n3. Assessing risk...")
risk_manager = RiskManager(
    max_position_size=0.1,
    max_leverage=3.0,
    stop_loss_pct=0.02,
)

returns = df["close"].pct_change().dropna()
risk_assessment = risk_manager.assess_portfolio_risk(returns)
print(f"   Historical VaR (95%): {risk_assessment['historical_var']:.4f}")
print(f"   Sharpe Ratio: {risk_assessment['sharpe_ratio']:.2f}")

# 4. Simple Moving Average Crossover Strategy
print("\n4. Running backtest with SMA crossover strategy...")

def sma_crossover_strategy(data):
    """Simple moving average crossover strategy."""
    if len(data) < 50:
        return "hold"
    
    sma_20 = data["close"].rolling(20).mean()
    sma_50 = data["close"].rolling(50).mean()
    
    if len(sma_20) < 2 or len(sma_50) < 2:
        return "hold"
    
    # Buy signal: SMA20 crosses above SMA50
    if sma_20.iloc[-2] <= sma_50.iloc[-2] and sma_20.iloc[-1] > sma_50.iloc[-1]:
        return "buy"
    
    # Sell signal: SMA20 crosses below SMA50
    if sma_20.iloc[-2] >= sma_50.iloc[-2] and sma_20.iloc[-1] < sma_50.iloc[-1]:
        return "sell"
    
    return "hold"

# Run backtest
backtester = Backtester(
    initial_capital=100000,
    commission_rate=0.001,
    slippage_rate=0.0005,
)

equity_curve_df = backtester.run(df, sma_crossover_strategy, symbol)
results = backtester.get_results()

# Calculate performance metrics
equity_series = equity_curve_df["total_equity"]
metrics = PerformanceMetrics.calculate_all_metrics(equity_series)

# 5. Display Results
print("\n" + "=" * 60)
print("Backtest Results")
print("=" * 60)
print(f"Initial Capital:     ${results['initial_capital']:,.2f}")
print(f"Final Equity:        ${results['final_equity']:,.2f}")
print(f"Total Return:        {results['total_return_pct']:.2f}%")
print(f"Total Trades:        {results['total_trades']}")
print(f"Sharpe Ratio:        {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown:        {metrics['max_drawdown_pct']:.2f}%")
print(f"Annual Return:       {metrics['annual_return']*100:.2f}%")
print(f"Annual Volatility:   {metrics['annual_volatility']*100:.2f}%")
print("=" * 60)

print("\n✓ Example completed successfully!")
print("\nNext steps:")
print("  - Configure your WEEX API credentials in .env")
print("  - Explore ML models in alphagenesis.models")
print("  - Customize strategies in your own scripts")
print("  - Check out notebooks/ for more examples")
