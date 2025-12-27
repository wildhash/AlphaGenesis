"""
Feature Engineering Module

This module provides tools for creating features from raw market data,
including technical indicators, statistical features, and market regime detection.

Components:
    - Technical indicators (RSI, MACD, Bollinger Bands, etc.)
    - Statistical features (volatility, momentum, etc.)
    - Market microstructure features
    - Market regime detection
    - Multi-timeframe confluence analysis
    - Custom feature generators
"""

from alphagenesis.features.technical_indicators import TechnicalIndicators
from alphagenesis.features.feature_engineer import FeatureEngineer
from alphagenesis.features.orderbook import OrderBookFeatureEngineer
from alphagenesis.features.temporal import TemporalFeatureEngineer
from alphagenesis.features.market_regime import (
    MarketRegimeDetector,
    RegimeType,
    RegimeState
)
from alphagenesis.features.confluence import (
    MultiTimeframeConfluence,
    ConfluenceResult,
    TrendDirection
)

__all__ = [
    "TechnicalIndicators",
    "FeatureEngineer",
    "OrderBookFeatureEngineer",
    "TemporalFeatureEngineer",
    "MarketRegimeDetector",
    "RegimeType",
    "RegimeState",
    "MultiTimeframeConfluence",
    "ConfluenceResult",
    "TrendDirection",
]
