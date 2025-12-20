"""
Order Book Feature Engineering

Creates features from order book data including imbalance, spread, and depth
metrics for alpha generation.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from loguru import logger


class OrderBookFeatureEngineer:
    """
    Engineers features from order book data.
    
    Calculates metrics such as:
    - Bid-ask spread
    - Order book imbalance
    - Market depth
    - Volume-weighted mid price
    - Liquidity indicators
    """
    
    def __init__(self, depth_levels: int = 10):
        """
        Initialize OrderBookFeatureEngineer.
        
        Args:
            depth_levels: Number of order book depth levels to analyze
        """
        self.depth_levels = depth_levels
        logger.info(f"OrderBookFeatureEngineer initialized with {depth_levels} depth levels")
    
    def create_features(
        self,
        orderbook: Dict[str, List[List[float]]],
        timestamp: Optional[pd.Timestamp] = None,
    ) -> Dict[str, float]:
        """
        Create order book features from snapshot.
        
        Args:
            orderbook: Order book data with 'bids' and 'asks' keys
                      Each is a list of [price, volume] pairs
            timestamp: Optional timestamp for the snapshot
            
        Returns:
            Dictionary of calculated features
        """
        features = {}
        
        try:
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if not bids or not asks:
                logger.warning("Empty order book, returning NaN features")
                return self._get_nan_features()
            
            # Limit to specified depth
            bids = bids[:self.depth_levels]
            asks = asks[:self.depth_levels]
            
            # Basic spread features
            features.update(self._calculate_spread_features(bids, asks))
            
            # Imbalance features
            features.update(self._calculate_imbalance_features(bids, asks))
            
            # Depth features
            features.update(self._calculate_depth_features(bids, asks))
            
            # Volume-weighted features
            features.update(self._calculate_volume_weighted_features(bids, asks))
            
            # Liquidity features
            features.update(self._calculate_liquidity_features(bids, asks))
            
        except Exception as e:
            logger.error(f"Error creating order book features: {e}")
            features = self._get_nan_features()
        
        return features
    
    def _calculate_spread_features(
        self,
        bids: List[List[float]],
        asks: List[List[float]],
    ) -> Dict[str, float]:
        """
        Calculate bid-ask spread related features.
        
        Args:
            bids: List of [price, volume] for bids
            asks: List of [price, volume] for asks
            
        Returns:
            Dictionary of spread features
        """
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        
        spread_abs = best_ask - best_bid
        mid_price = (best_bid + best_ask) / 2.0
        spread_bps = (spread_abs / mid_price) * 10000  # Basis points
        
        return {
            'ob_spread_abs': spread_abs,
            'ob_spread_bps': spread_bps,
            'ob_mid_price': mid_price,
            'ob_best_bid': best_bid,
            'ob_best_ask': best_ask,
        }
    
    def _calculate_imbalance_features(
        self,
        bids: List[List[float]],
        asks: List[List[float]],
    ) -> Dict[str, float]:
        """
        Calculate order book imbalance features.
        
        Imbalance indicates buying vs selling pressure in the order book.
        
        Args:
            bids: List of [price, volume] for bids
            asks: List of [price, volume] for asks
            
        Returns:
            Dictionary of imbalance features
        """
        # Calculate total volumes
        bid_volume = sum(level[1] for level in bids)
        ask_volume = sum(level[1] for level in asks)
        total_volume = bid_volume + ask_volume
        
        # Volume imbalance ratio
        if total_volume > 0:
            volume_imbalance = (bid_volume - ask_volume) / total_volume
        else:
            volume_imbalance = 0.0
        
        # Top level imbalance
        top_bid_volume = bids[0][1] if bids else 0
        top_ask_volume = asks[0][1] if asks else 0
        top_total = top_bid_volume + top_ask_volume
        
        if top_total > 0:
            top_imbalance = (top_bid_volume - top_ask_volume) / top_total
        else:
            top_imbalance = 0.0
        
        # Weighted imbalance (closer levels have more weight)
        weights = np.exp(-np.arange(len(bids)) * 0.1)
        bid_weighted_vol = sum(bids[i][1] * weights[i] for i in range(len(bids)))
        ask_weighted_vol = sum(asks[i][1] * weights[i] for i in range(len(asks)))
        weighted_total = bid_weighted_vol + ask_weighted_vol
        
        if weighted_total > 0:
            weighted_imbalance = (bid_weighted_vol - ask_weighted_vol) / weighted_total
        else:
            weighted_imbalance = 0.0
        
        return {
            'ob_volume_imbalance': volume_imbalance,
            'ob_top_imbalance': top_imbalance,
            'ob_weighted_imbalance': weighted_imbalance,
            'ob_bid_volume': bid_volume,
            'ob_ask_volume': ask_volume,
        }
    
    def _calculate_depth_features(
        self,
        bids: List[List[float]],
        asks: List[List[float]],
    ) -> Dict[str, float]:
        """
        Calculate market depth features.
        
        Args:
            bids: List of [price, volume] for bids
            asks: List of [price, volume] for asks
            
        Returns:
            Dictionary of depth features
        """
        # Price ranges
        if len(bids) > 1 and len(asks) > 1:
            bid_range = bids[0][0] - bids[-1][0]
            ask_range = asks[-1][0] - asks[0][0]
            total_range = asks[-1][0] - bids[-1][0]
        else:
            bid_range = ask_range = total_range = 0.0
        
        # Volume at different depths
        bid_vol_top5 = sum(bids[i][1] for i in range(min(5, len(bids))))
        ask_vol_top5 = sum(asks[i][1] for i in range(min(5, len(asks))))
        
        # Depth quality - how evenly distributed is volume
        bid_volumes = [level[1] for level in bids]
        ask_volumes = [level[1] for level in asks]
        
        bid_vol_std = np.std(bid_volumes) if len(bid_volumes) > 1 else 0.0
        ask_vol_std = np.std(ask_volumes) if len(ask_volumes) > 1 else 0.0
        
        return {
            'ob_bid_range': bid_range,
            'ob_ask_range': ask_range,
            'ob_total_range': total_range,
            'ob_bid_vol_top5': bid_vol_top5,
            'ob_ask_vol_top5': ask_vol_top5,
            'ob_bid_vol_std': bid_vol_std,
            'ob_ask_vol_std': ask_vol_std,
        }
    
    def _calculate_volume_weighted_features(
        self,
        bids: List[List[float]],
        asks: List[List[float]],
    ) -> Dict[str, float]:
        """
        Calculate volume-weighted price features.
        
        Args:
            bids: List of [price, volume] for bids
            asks: List of [price, volume] for asks
            
        Returns:
            Dictionary of volume-weighted features
        """
        # Volume-weighted bid price
        bid_volume_total = sum(level[1] for level in bids)
        if bid_volume_total > 0:
            vwap_bid = sum(level[0] * level[1] for level in bids) / bid_volume_total
        else:
            vwap_bid = bids[0][0] if bids else 0.0
        
        # Volume-weighted ask price
        ask_volume_total = sum(level[1] for level in asks)
        if ask_volume_total > 0:
            vwap_ask = sum(level[0] * level[1] for level in asks) / ask_volume_total
        else:
            vwap_ask = asks[0][0] if asks else 0.0
        
        # Volume-weighted mid price
        vwap_mid = (vwap_bid + vwap_ask) / 2.0
        
        # VWAP spread
        vwap_spread = vwap_ask - vwap_bid
        
        return {
            'ob_vwap_bid': vwap_bid,
            'ob_vwap_ask': vwap_ask,
            'ob_vwap_mid': vwap_mid,
            'ob_vwap_spread': vwap_spread,
        }
    
    def _calculate_liquidity_features(
        self,
        bids: List[List[float]],
        asks: List[List[float]],
    ) -> Dict[str, float]:
        """
        Calculate liquidity indicators.
        
        Args:
            bids: List of [price, volume] for bids
            asks: List of [price, volume] for asks
            
        Returns:
            Dictionary of liquidity features
        """
        # Count of price levels
        n_bid_levels = len(bids)
        n_ask_levels = len(asks)
        
        # Average size per level
        avg_bid_size = np.mean([level[1] for level in bids]) if bids else 0.0
        avg_ask_size = np.mean([level[1] for level in asks]) if asks else 0.0
        
        # Concentration - what % of volume is in top level
        bid_volume_total = sum(level[1] for level in bids)
        ask_volume_total = sum(level[1] for level in asks)
        
        if bid_volume_total > 0:
            bid_concentration = bids[0][1] / bid_volume_total
        else:
            bid_concentration = 0.0
        
        if ask_volume_total > 0:
            ask_concentration = asks[0][1] / ask_volume_total
        else:
            ask_concentration = 0.0
        
        return {
            'ob_n_bid_levels': n_bid_levels,
            'ob_n_ask_levels': n_ask_levels,
            'ob_avg_bid_size': avg_bid_size,
            'ob_avg_ask_size': avg_ask_size,
            'ob_bid_concentration': bid_concentration,
            'ob_ask_concentration': ask_concentration,
        }
    
    def _get_nan_features(self) -> Dict[str, float]:
        """
        Return dictionary of NaN features when calculation fails.
        
        Returns:
            Dictionary with all features set to NaN
        """
        return {
            'ob_spread_abs': np.nan,
            'ob_spread_bps': np.nan,
            'ob_mid_price': np.nan,
            'ob_best_bid': np.nan,
            'ob_best_ask': np.nan,
            'ob_volume_imbalance': np.nan,
            'ob_top_imbalance': np.nan,
            'ob_weighted_imbalance': np.nan,
            'ob_bid_volume': np.nan,
            'ob_ask_volume': np.nan,
            'ob_bid_range': np.nan,
            'ob_ask_range': np.nan,
            'ob_total_range': np.nan,
            'ob_bid_vol_top5': np.nan,
            'ob_ask_vol_top5': np.nan,
            'ob_bid_vol_std': np.nan,
            'ob_ask_vol_std': np.nan,
            'ob_vwap_bid': np.nan,
            'ob_vwap_ask': np.nan,
            'ob_vwap_mid': np.nan,
            'ob_vwap_spread': np.nan,
            'ob_n_bid_levels': np.nan,
            'ob_n_ask_levels': np.nan,
            'ob_avg_bid_size': np.nan,
            'ob_avg_ask_size': np.nan,
            'ob_bid_concentration': np.nan,
            'ob_ask_concentration': np.nan,
        }
    
    def create_time_series_features(
        self,
        orderbook_history: List[Dict[str, List[List[float]]]],
        timestamps: List[pd.Timestamp],
    ) -> pd.DataFrame:
        """
        Create time series of order book features.
        
        Args:
            orderbook_history: List of order book snapshots
            timestamps: Corresponding timestamps
            
        Returns:
            DataFrame with time series of order book features
        """
        features_list = []
        
        for orderbook, timestamp in zip(orderbook_history, timestamps):
            features = self.create_features(orderbook, timestamp)
            features['timestamp'] = timestamp
            features_list.append(features)
        
        df = pd.DataFrame(features_list)
        df.set_index('timestamp', inplace=True)
        
        logger.info(f"Created order book feature time series with {len(df)} rows")
        
        return df
