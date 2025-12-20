"""
Basic tests for AlphaGenesis modules
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def test_imports():
    """Test that all modules can be imported."""
    from alphagenesis import data, features, models, risk, backtest, execution, utils
    
    assert data is not None
    assert features is not None
    assert models is not None
    assert risk is not None
    assert backtest is not None
    assert execution is not None
    assert utils is not None


def test_feature_engineering():
    """Test feature engineering functionality."""
    from alphagenesis.features import FeatureEngineer
    
    # Create sample data
    dates = pd.date_range(end=datetime.now(), periods=100, freq="1H")
    df = pd.DataFrame({
        "open": np.random.randn(100).cumsum() + 100,
        "high": np.random.randn(100).cumsum() + 101,
        "low": np.random.randn(100).cumsum() + 99,
        "close": np.random.randn(100).cumsum() + 100,
        "volume": np.random.randint(1000, 10000, 100),
    }, index=dates)
    
    fe = FeatureEngineer()
    result = fe.create_features(df)
    
    assert len(result) == len(df)
    assert "rsi_14" in result.columns
    assert "macd" in result.columns


def test_var_calculator():
    """Test VaR calculation."""
    from alphagenesis.risk import VaRCalculator
    
    returns = np.random.randn(1000) * 0.01
    
    var_calc = VaRCalculator()
    var = var_calc.historical_var(returns, confidence_level=0.95)
    
    assert var >= 0
    assert isinstance(var, float)


def test_backtester():
    """Test basic backtester functionality."""
    from alphagenesis.backtest import Backtester
    
    # Create sample data
    dates = pd.date_range(end=datetime.now(), periods=100, freq="1H")
    df = pd.DataFrame({
        "open": np.random.randn(100).cumsum() + 100,
        "high": np.random.randn(100).cumsum() + 101,
        "low": np.random.randn(100).cumsum() + 99,
        "close": np.random.randn(100).cumsum() + 100,
        "volume": np.random.randint(1000, 10000, 100),
    }, index=dates)
    
    backtester = Backtester(initial_capital=100000)
    
    def simple_strategy(data):
        return "hold"
    
    equity_curve = backtester.run(df, simple_strategy)
    
    assert not equity_curve.empty
    assert "total_equity" in equity_curve.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
