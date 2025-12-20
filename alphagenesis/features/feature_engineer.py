"""
Feature Engineer Module

Orchestrates the creation of features from raw market data for ML models.
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from loguru import logger

from alphagenesis.features.technical_indicators import TechnicalIndicators


class FeatureEngineer:
    """
    Creates features for machine learning models from market data.
    
    Combines technical indicators, statistical features, and custom
    transformations to prepare data for predictive models.
    """
    
    def __init__(self):
        """Initialize feature engineer."""
        self.indicators = TechnicalIndicators()
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive feature set from OHLCV data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added features
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for feature engineering")
            return df
        
        features_df = df.copy()
        
        try:
            # Price-based features
            features_df["returns"] = df["close"].pct_change()
            features_df["log_returns"] = np.log(df["close"] / df["close"].shift(1))
            
            # Volatility features
            features_df["volatility_5"] = features_df["returns"].rolling(5).std()
            features_df["volatility_20"] = features_df["returns"].rolling(20).std()
            
            # Momentum features
            features_df["momentum_5"] = df["close"] / df["close"].shift(5) - 1
            features_df["momentum_20"] = df["close"] / df["close"].shift(20) - 1
            
            # Technical indicators
            features_df["rsi_14"] = self.indicators.calculate_rsi(df["close"], 14)
            
            macd = self.indicators.calculate_macd(df["close"])
            features_df["macd"] = macd["macd"]
            features_df["macd_signal"] = macd["signal"]
            features_df["macd_histogram"] = macd["histogram"]
            
            bb = self.indicators.calculate_bollinger_bands(df["close"])
            features_df["bb_upper"] = bb["upper"]
            features_df["bb_middle"] = bb["middle"]
            features_df["bb_lower"] = bb["lower"]
            features_df["bb_width"] = (bb["upper"] - bb["lower"]) / bb["middle"]
            
            # Moving averages
            for period in [5, 10, 20, 50, 200]:
                features_df[f"sma_{period}"] = self.indicators.calculate_sma(df["close"], period)
                features_df[f"ema_{period}"] = self.indicators.calculate_ema(df["close"], period)
            
            # Volume features
            if "volume" in df.columns:
                features_df["volume_sma_20"] = df["volume"].rolling(20).mean()
                features_df["volume_ratio"] = df["volume"] / features_df["volume_sma_20"]
            
            # ATR
            if all(col in df.columns for col in ["high", "low", "close"]):
                features_df["atr_14"] = self.indicators.calculate_atr(
                    df["high"], df["low"], df["close"], 14
                )
            
            logger.info(f"Created {len(features_df.columns) - len(df.columns)} new features")
            
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
        
        return features_df
    
    def create_target(
        self,
        df: pd.DataFrame,
        target_column: str = "close",
        horizon: int = 1,
        threshold: float = 0.0,
    ) -> pd.Series:
        """
        Create target variable for supervised learning.
        
        Args:
            df: DataFrame with price data
            target_column: Column to use for target
            horizon: Prediction horizon (periods ahead)
            threshold: Classification threshold
            
        Returns:
            Target series
        """
        future_returns = df[target_column].pct_change(horizon).shift(-horizon)
        
        # Binary classification: 1 if price increases, 0 otherwise
        target = (future_returns > threshold).astype(int)
        
        return target
