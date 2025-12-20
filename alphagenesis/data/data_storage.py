"""
Data Storage Module

Handles persistent storage and caching of market data.
Supports multiple storage backends including databases and file systems.
"""

from typing import Optional, Any
from pathlib import Path
import pandas as pd
from loguru import logger


class DataStorage:
    """
    Manages data storage and retrieval for the trading system.
    
    Provides efficient storage and caching mechanisms for historical data.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize data storage.
        
        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = Path(storage_path or "./data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_dataframe(
        self,
        df: pd.DataFrame,
        filename: str,
        format: str = "parquet",
    ) -> None:
        """
        Save DataFrame to storage.
        
        Args:
            df: DataFrame to save
            filename: Name of the file
            format: Storage format (parquet, csv, hdf5)
        """
        filepath = self.storage_path / filename
        
        try:
            if format == "parquet":
                df.to_parquet(filepath)
            elif format == "csv":
                df.to_csv(filepath)
            elif format == "hdf5":
                df.to_hdf(filepath, key="data", mode="w")
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Saved data to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            raise
    
    def load_dataframe(
        self,
        filename: str,
        format: str = "parquet",
    ) -> pd.DataFrame:
        """
        Load DataFrame from storage.
        
        Args:
            filename: Name of the file
            format: Storage format
            
        Returns:
            Loaded DataFrame
        """
        filepath = self.storage_path / filename
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return pd.DataFrame()
        
        try:
            if format == "parquet":
                return pd.read_parquet(filepath)
            elif format == "csv":
                return pd.read_csv(filepath, index_col=0, parse_dates=True)
            elif format == "hdf5":
                return pd.read_hdf(filepath, key="data")
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return pd.DataFrame()
