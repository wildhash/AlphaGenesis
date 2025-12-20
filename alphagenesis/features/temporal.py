"""
Temporal Feature Engineering

Creates time-based features such as hour of day, day of week, and other
temporal patterns that can affect market behavior.
"""

from typing import Optional, List
import pandas as pd
import numpy as np
from loguru import logger


class TemporalFeatureEngineer:
    """
    Engineers temporal features from datetime index.
    
    Creates features capturing:
    - Hour of day effects (trading session patterns)
    - Day of week effects
    - Month/quarter effects
    - Weekend/holiday proximity
    - Market session indicators
    """
    
    def __init__(
        self,
        market_open_hour: int = 0,
        market_close_hour: int = 24,
        include_cyclical: bool = True,
    ):
        """
        Initialize TemporalFeatureEngineer.
        
        Args:
            market_open_hour: Market opening hour (UTC)
            market_close_hour: Market closing hour (UTC)
            include_cyclical: Whether to include cyclical encoding of temporal features
        """
        self.market_open_hour = market_open_hour
        self.market_close_hour = market_close_hour
        self.include_cyclical = include_cyclical
        
        logger.info(
            f"TemporalFeatureEngineer initialized: "
            f"market_hours={market_open_hour}-{market_close_hour}, "
            f"cyclical={include_cyclical}"
        )
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create temporal features from DataFrame with DatetimeIndex.
        
        Args:
            df: DataFrame with DatetimeIndex
            
        Returns:
            DataFrame with added temporal features
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            logger.warning("DataFrame index is not DatetimeIndex, attempting conversion")
            try:
                df.index = pd.to_datetime(df.index)
            except Exception as e:
                logger.error(f"Failed to convert index to datetime: {e}")
                return df
        
        df_features = df.copy()
        
        logger.info("Creating temporal features")
        
        # Basic time components
        df_features['hour'] = df_features.index.hour
        df_features['day_of_week'] = df_features.index.dayofweek  # Monday=0, Sunday=6
        df_features['day_of_month'] = df_features.index.day
        df_features['month'] = df_features.index.month
        df_features['quarter'] = df_features.index.quarter
        df_features['year'] = df_features.index.year
        
        # Week features
        df_features['week_of_year'] = df_features.index.isocalendar().week
        df_features['is_weekend'] = (df_features['day_of_week'] >= 5).astype(int)
        
        # Month features
        df_features['is_month_start'] = df_features.index.is_month_start.astype(int)
        df_features['is_month_end'] = df_features.index.is_month_end.astype(int)
        df_features['is_quarter_start'] = df_features.index.is_quarter_start.astype(int)
        df_features['is_quarter_end'] = df_features.index.is_quarter_end.astype(int)
        
        # Market session features (for crypto, 24/7, but patterns exist)
        df_features['is_asian_session'] = ((df_features['hour'] >= 0) & (df_features['hour'] < 8)).astype(int)
        df_features['is_european_session'] = ((df_features['hour'] >= 8) & (df_features['hour'] < 16)).astype(int)
        df_features['is_american_session'] = ((df_features['hour'] >= 16) & (df_features['hour'] < 24)).astype(int)
        
        # Traditional market overlap periods (high liquidity)
        df_features['is_london_ny_overlap'] = ((df_features['hour'] >= 13) & (df_features['hour'] < 17)).astype(int)
        df_features['is_sydney_tokyo_overlap'] = ((df_features['hour'] >= 0) & (df_features['hour'] < 2)).astype(int)
        
        # Cyclical encoding (important for neural networks)
        if self.include_cyclical:
            # Hour (24-hour cycle)
            df_features['hour_sin'] = np.sin(2 * np.pi * df_features['hour'] / 24)
            df_features['hour_cos'] = np.cos(2 * np.pi * df_features['hour'] / 24)
            
            # Day of week (7-day cycle)
            df_features['day_sin'] = np.sin(2 * np.pi * df_features['day_of_week'] / 7)
            df_features['day_cos'] = np.cos(2 * np.pi * df_features['day_of_week'] / 7)
            
            # Month (12-month cycle)
            df_features['month_sin'] = np.sin(2 * np.pi * df_features['month'] / 12)
            df_features['month_cos'] = np.cos(2 * np.pi * df_features['month'] / 12)
            
            # Day of month (approximate 30-day cycle)
            df_features['day_of_month_sin'] = np.sin(2 * np.pi * df_features['day_of_month'] / 30)
            df_features['day_of_month_cos'] = np.cos(2 * np.pi * df_features['day_of_month'] / 30)
        
        # Time since epoch (useful for trend)
        df_features['timestamp_seconds'] = df_features.index.astype(np.int64) // 10**9
        
        # Normalized time features (0-1 range)
        df_features['hour_normalized'] = df_features['hour'] / 24.0
        df_features['day_of_week_normalized'] = df_features['day_of_week'] / 7.0
        df_features['month_normalized'] = df_features['month'] / 12.0
        
        logger.info(f"Created {len(df_features.columns) - len(df.columns)} temporal features")
        
        return df_features
    
    def create_lagged_temporal_features(
        self,
        df: pd.DataFrame,
        lags: Optional[List[int]] = None,
    ) -> pd.DataFrame:
        """
        Create lagged versions of temporal features.
        
        Useful for capturing patterns like "hour of day 1 hour ago".
        
        Args:
            df: DataFrame with temporal features
            lags: List of lag periods (default: [1, 2, 3, 6, 12, 24])
            
        Returns:
            DataFrame with lagged temporal features
        """
        if lags is None:
            lags = [1, 2, 3, 6, 12, 24]
        
        df_lagged = df.copy()
        
        # Features to lag
        temporal_cols = ['hour', 'day_of_week', 'is_weekend', 
                        'is_asian_session', 'is_european_session', 'is_american_session']
        
        existing_cols = [col for col in temporal_cols if col in df.columns]
        
        for col in existing_cols:
            for lag in lags:
                lagged_col_name = f'{col}_lag_{lag}'
                df_lagged[lagged_col_name] = df_lagged[col].shift(lag)
        
        logger.info(f"Created lagged temporal features with lags: {lags}")
        
        return df_lagged
    
    def create_volatility_regime_features(
        self,
        df: pd.DataFrame,
        price_col: str = 'close',
        window: int = 24,
    ) -> pd.DataFrame:
        """
        Create features indicating volatility regime at different times.
        
        Args:
            df: DataFrame with price data
            price_col: Name of price column
            window: Rolling window for volatility calculation
            
        Returns:
            DataFrame with volatility regime features
        """
        df_vol = df.copy()
        
        if price_col not in df.columns:
            logger.warning(f"Price column '{price_col}' not found, skipping volatility features")
            return df_vol
        
        # Calculate returns
        returns = df_vol[price_col].pct_change()
        
        # Rolling volatility
        rolling_vol = returns.rolling(window=window).std()
        
        # Volatility by hour
        df_vol['vol_by_hour'] = returns.groupby(df_vol.index.hour).transform('std')
        
        # Volatility by day of week
        df_vol['vol_by_day'] = returns.groupby(df_vol.index.dayofweek).transform('std')
        
        # Current vol vs historical vol
        df_vol['vol_ratio_hour'] = rolling_vol / df_vol['vol_by_hour']
        df_vol['vol_ratio_day'] = rolling_vol / df_vol['vol_by_day']
        
        # High/low volatility regime indicators
        vol_percentile = rolling_vol.rank(pct=True)
        df_vol['is_high_vol_regime'] = (vol_percentile > 0.75).astype(int)
        df_vol['is_low_vol_regime'] = (vol_percentile < 0.25).astype(int)
        
        logger.info("Created volatility regime features")
        
        return df_vol
    
    def create_event_proximity_features(
        self,
        df: pd.DataFrame,
        event_dates: Optional[List[pd.Timestamp]] = None,
    ) -> pd.DataFrame:
        """
        Create features for proximity to known events (e.g., FOMC, expiry dates).
        
        Args:
            df: DataFrame with DatetimeIndex
            event_dates: List of event timestamps
            
        Returns:
            DataFrame with event proximity features
        """
        df_events = df.copy()
        
        if event_dates is None or len(event_dates) == 0:
            logger.info("No event dates provided, skipping event proximity features")
            return df_events
        
        # Days until next event
        def days_until_next_event(timestamp):
            future_events = [e for e in event_dates if e > timestamp]
            if future_events:
                return (min(future_events) - timestamp).days
            return np.nan
        
        # Days since last event
        def days_since_last_event(timestamp):
            past_events = [e for e in event_dates if e <= timestamp]
            if past_events:
                return (timestamp - max(past_events)).days
            return np.nan
        
        df_events['days_until_event'] = df_events.index.map(days_until_next_event)
        df_events['days_since_event'] = df_events.index.map(days_since_last_event)
        
        # Is within N days of event
        for n in [1, 3, 7]:
            df_events[f'is_within_{n}d_of_event'] = (
                (df_events['days_until_event'] <= n) | 
                (df_events['days_since_event'] <= n)
            ).astype(int)
        
        logger.info(f"Created event proximity features for {len(event_dates)} events")
        
        return df_events
    
    def get_feature_names(self) -> List[str]:
        """
        Get list of all temporal feature names that will be created.
        
        Returns:
            List of feature names
        """
        features = [
            'hour', 'day_of_week', 'day_of_month', 'month', 'quarter', 'year',
            'week_of_year', 'is_weekend', 'is_month_start', 'is_month_end',
            'is_quarter_start', 'is_quarter_end', 'is_asian_session',
            'is_european_session', 'is_american_session', 'is_london_ny_overlap',
            'is_sydney_tokyo_overlap', 'timestamp_seconds', 'hour_normalized',
            'day_of_week_normalized', 'month_normalized',
        ]
        
        if self.include_cyclical:
            features.extend([
                'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
                'month_sin', 'month_cos', 'day_of_month_sin', 'day_of_month_cos',
            ])
        
        return features
