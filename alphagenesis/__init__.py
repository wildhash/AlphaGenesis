"""
AlphaGenesis: An institutional-grade, AI-powered quantitative trading system.

Built for the WEEX AI Wars Hackathon - implementing DeepSeek's winning strategy.

Key Features:
    - DeepSeek-inspired reasoning layer for disciplined decision making
    - Advanced ML models (LSTM, Transformers, Reinforcement Learning)
    - Multi-timeframe confluence analysis
    - Market regime detection
    - Sophisticated risk management (VaR, GARCH, portfolio optimization)
    - Event-driven backtesting engine
    - Real-time market data processing and order execution

Modules:
    ai: DeepSeek reasoning layer and AI decision making
    data: Data pipeline and WEEX API integration
    features: Feature engineering, regime detection, and confluence
    models: Machine learning models and predictive algorithms
    risk: Risk management and portfolio optimization
    backtest: Event-driven backtesting framework
    execution: Order execution and management
    utils: Utility functions and helpers
"""

__version__ = "0.2.0"
__author__ = "AlphaGenesis Team"
__license__ = "MIT"

from alphagenesis import (
    ai,
    data,
    features,
    models,
    risk,
    backtest,
    execution,
    utils,
)

__all__ = [
    "ai",
    "data",
    "features",
    "models",
    "risk",
    "backtest",
    "execution",
    "utils",
]
