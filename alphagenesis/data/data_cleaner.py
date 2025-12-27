"""
Data Cleaning and Preprocessing Module

Handles missing values, outliers, and ensures point-in-time data processing
to prevent look-ahead bias in backtesting and live trading.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from loguru import logger


class DataCleaner:
    """
    Data cleaning and preprocessing for financial time series.
    
    Ensures data integrity and point-in-time correctness for backtesting
    and live trading to avoid look-ahead bias.
    """
    
    def __init__(
        self,
        fill_method: str = "ffill",
        max_fill_gap: int = 5,
        outlier_std: float = 5.0,
    ):
        """
        Initialize DataCleaner.
        
        Args:
            fill_method: Method for filling missing values ('ffill', 'bfill', 'interpolate')
            max_fill_gap: Maximum number of consecutive NaN values to fill
            outlier_std: Number of standard deviations for outlier detection
        """
        self.fill_method = fill_method
        self.max_fill_gap = max_fill_gap
        self.outlier_std = outlier_std
        
        logger.info(
            f"DataCleaner initialized: fill_method={fill_method}, "
            f"max_fill_gap={max_fill_gap}, outlier_std={outlier_std}"
        )
    
    def clean(
        self,
        df: pd.DataFrame,
        handle_missing: bool = True,
        handle_outliers: bool = True,
        handle_duplicates: bool = True,
    ) -> pd.DataFrame:
        """
        Clean financial time series data.
        
        Args:
            df: Input DataFrame with time series data
            handle_missing: Whether to handle missing values
            handle_outliers: Whether to handle outliers
            handle_duplicates: Whether to handle duplicate timestamps
            
        Returns:
            Cleaned DataFrame
        """
        df_clean = df.copy()
        
        logger.info(f"Starting data cleaning. Original shape: {df_clean.shape}")
        
        # Handle duplicates first
        if handle_duplicates:
            df_clean = self._remove_duplicates(df_clean)
        
        # Handle missing values
        if handle_missing:
            df_clean = self._handle_missing_values(df_clean)
        
        # Handle outliers
        if handle_outliers:
            df_clean = self._handle_outliers(df_clean)
        
        # Validate point-in-time correctness
        df_clean = self._ensure_point_in_time(df_clean)
        
        logger.info(f"Data cleaning complete. Final shape: {df_clean.shape}")
        
        return df_clean
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate timestamps, keeping the first occurrence.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame without duplicates
        """
        n_duplicates = df.index.duplicated().sum()
        
        if n_duplicates > 0:
            logger.warning(f"Found {n_duplicates} duplicate timestamps, removing...")
            df = df[~df.index.duplicated(keep='first')]
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values using point-in-time safe methods.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with missing values handled
        """
        # Check for missing values
        missing_counts = df.isnull().sum()
        total_missing = missing_counts.sum()
        
        if total_missing > 0:
            logger.info(f"Found {total_missing} missing values")
            
            for col in df.columns:
                if missing_counts[col] > 0:
                    logger.debug(f"Column '{col}' has {missing_counts[col]} missing values")
                    
                    # Use point-in-time safe filling (forward fill only)
                    if self.fill_method == "ffill":
                        df[col] = df[col].fillna(method='ffill', limit=self.max_fill_gap)
                    elif self.fill_method == "interpolate":
                        # Linear interpolation is safe if we limit it
                        df[col] = df[col].interpolate(method='linear', limit=self.max_fill_gap)
                    
                    # Fill remaining NaN at start with first valid value
                    first_valid = df[col].first_valid_index()
                    if first_valid is not None:
                        first_value = df.loc[first_valid, col]
                        df[col].fillna(first_value, inplace=True)
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect and handle outliers using statistical methods.
        
        Uses rolling statistics to detect outliers while maintaining
        point-in-time correctness.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with outliers handled
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Calculate rolling statistics (point-in-time safe)
            rolling_mean = df[col].rolling(window=20, min_periods=1).mean()
            rolling_std = df[col].rolling(window=20, min_periods=1).std()
            
            # Identify outliers
            upper_bound = rolling_mean + self.outlier_std * rolling_std
            lower_bound = rolling_mean - self.outlier_std * rolling_std
            
            outliers = (df[col] > upper_bound) | (df[col] < lower_bound)
            n_outliers = outliers.sum()
            
            if n_outliers > 0:
                logger.debug(f"Found {n_outliers} outliers in column '{col}'")
                
                # Clip outliers to bounds (conservative approach)
                df.loc[df[col] > upper_bound, col] = upper_bound[df[col] > upper_bound]
                df.loc[df[col] < lower_bound, col] = lower_bound[df[col] < lower_bound]
        
        return df
    
    def _ensure_point_in_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure data is properly sorted and indexed for point-in-time correctness.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with proper time ordering
        """
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            logger.warning("Index is not DatetimeIndex, attempting conversion")
            try:
                df.index = pd.to_datetime(df.index)
            except Exception as e:
                logger.error(f"Failed to convert index to datetime: {e}")
        
        # Sort by index to ensure chronological order
        if not df.index.is_monotonic_increasing:
            logger.info("Sorting data chronologically")
            df = df.sort_index()
        
        return df
    
    def validate_data_integrity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate data integrity and return diagnostic information.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "shape": df.shape,
            "missing_values": df.isnull().sum().to_dict(),
            "duplicate_timestamps": df.index.duplicated().sum(),
            "time_sorted": df.index.is_monotonic_increasing,
            "date_range": {
                "start": df.index.min(),
                "end": df.index.max(),
            },
            "columns": list(df.columns),
        }
        
        # Check for common data quality issues
        issues = []
        
        missing_total = sum(validation_results["missing_values"].values())
        validation_results["missing_values_total"] = missing_total
        if missing_total:
            issues.append(f"Found {missing_total} missing values")
        
        if validation_results["duplicate_timestamps"] > 0:
            issues.append(f"Found {validation_results['duplicate_timestamps']} duplicate timestamps")
        
        if not validation_results["time_sorted"]:
            issues.append("Data is not chronologically sorted")
        
        validation_results["issues"] = issues
        validation_results["is_valid"] = len(issues) == 0
        
        if issues:
            logger.warning(f"Data validation found {len(issues)} issues: {issues}")
        else:
            logger.info("Data validation passed")
        
        return validation_results
    
    def resample_ohlcv(
        self,
        df: pd.DataFrame,
        target_freq: str,
        ohlc_cols: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """
        Resample OHLCV data to a different frequency.
        
        Args:
            df: DataFrame with OHLCV data
            target_freq: Target frequency (e.g., '5T', '1H', '1D')
            ohlc_cols: Column name mapping {'open': 'Open', 'high': 'High', ...}
            
        Returns:
            Resampled DataFrame
        """
        if ohlc_cols is None:
            ohlc_cols = {
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
        
        logger.info(f"Resampling data to {target_freq}")
        
        # Define aggregation rules
        agg_dict = {
            ohlc_cols['open']: 'first',
            ohlc_cols['high']: 'max',
            ohlc_cols['low']: 'min',
            ohlc_cols['close']: 'last',
        }
        
        if 'volume' in ohlc_cols:
            agg_dict[ohlc_cols['volume']] = 'sum'
        
        # Resample
        df_resampled = df.resample(target_freq).agg(agg_dict)
        
        # Drop rows with NaN (no data in that period)
        df_resampled = df_resampled.dropna()
        
        logger.info(f"Resampled from {len(df)} to {len(df_resampled)} rows")
        
        return df_resampled
