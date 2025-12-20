"""
AlphaGenesis: An institutional-grade, AI-powered quantitative trading system.

This package provides a comprehensive framework for developing and deploying
AI-driven quantitative trading strategies in cryptocurrency markets, with
specific integration for the WEEX exchange API.

Key Features:
    - Advanced ML models (LSTM, Transformers, Reinforcement Learning)
    - Sophisticated risk management (VaR, GARCH, portfolio optimization)
    - Event-driven backtesting engine
    - Modular architecture for data pipeline, feature engineering, and execution
    - Real-time market data processing and order execution

Modules:
    data: Data pipeline and WEEX API integration
    features: Feature engineering and technical indicators
    models: Machine learning models and predictive algorithms
    risk: Risk management and portfolio optimization
    backtest: Event-driven backtesting framework
    execution: Order execution and management
    utils: Utility functions and helpers
"""

__version__ = "0.1.0"
__author__ = "AlphaGenesis Team"
__license__ = "MIT"

from alphagenesis import (
    data,
    features,
    models,
    risk,
    backtest,
    execution,
    utils,
)

__all__ = [
    "data",
    "features",
    "models",
    "risk",
    "backtest",
    "execution",
    "utils",
]
