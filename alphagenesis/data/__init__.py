"""
Data Pipeline Module

This module handles data acquisition, preprocessing, and storage for the trading system.
Includes integration with WEEX exchange API and other data sources.

Components:
    - WEEX API client for real-time and historical data
    - Data fetchers for market data, order book, trades
    - Data storage and caching mechanisms
    - Data validation and cleaning utilities
"""

from alphagenesis.data.weex_client import WEEXClient
from alphagenesis.data.data_fetcher import DataFetcher
from alphagenesis.data.data_storage import DataStorage

__all__ = [
    "WEEXClient",
    "DataFetcher",
    "DataStorage",
]
