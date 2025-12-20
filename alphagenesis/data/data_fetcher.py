"""
Data Fetcher Module

Handles data fetching, preprocessing, and management from various sources.
Provides a unified interface for accessing historical and real-time market data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from alphagenesis.data.weex_client import WEEXClient


class DataFetcher:
    """
    Fetches and preprocesses market data for the trading system.
    
    Coordinates data acquisition from multiple sources and ensures
    data quality and consistency.
    """
    
    def __init__(self, weex_client: Optional[WEEXClient] = None):
        """
        Initialize data fetcher.
        
        Args:
            weex_client: WEEX API client instance
        """
        self.weex_client = weex_client or WEEXClient()
    
    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str = "1h",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a given symbol and time range.
        
        Args:
            symbol: Trading pair symbol
            interval: Candlestick interval
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            data = self.weex_client.get_market_data(symbol, interval)
            df = pd.DataFrame(data)
            
            if not df.empty and "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df.set_index("timestamp", inplace=True)
                df.sort_index(inplace=True)
            
            logger.info(f"Fetched {len(df)} OHLCV records for {symbol}")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV data: {e}")
            return pd.DataFrame()
    
    def fetch_orderbook(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        """
        Fetch current order book for a symbol.
        
        Args:
            symbol: Trading pair symbol
            depth: Order book depth
            
        Returns:
            Order book data
        """
        try:
            return self.weex_client.get_orderbook(symbol, depth)
        except Exception as e:
            logger.error(f"Failed to fetch order book: {e}")
            return {"bids": [], "asks": []}
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean market data.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Cleaned DataFrame
        """
        # Remove duplicates
        df = df[~df.index.duplicated(keep="first")]
        
        # Remove rows with missing critical data
        required_columns = ["open", "high", "low", "close", "volume"]
        df = df.dropna(subset=[col for col in required_columns if col in df.columns])
        
        # Ensure proper data types
        numeric_columns = ["open", "high", "low", "close", "volume"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        logger.debug(f"Validated data: {len(df)} records remain after cleaning")
        return df
