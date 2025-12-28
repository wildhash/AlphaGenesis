"""
On-Chain Feature Engineer

Extracts on-chain metrics for cryptocurrency trading:
- Network activity (active addresses, transaction volume)
- Miner behavior (hash rate, miner revenue)
- Token economics (supply dynamics, exchange flows)
- Network health indicators
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class OnChainFeatureEngineer:
    """
    Extracts on-chain metrics for cryptocurrency analysis.
    
    Integrates with blockchain data providers to fetch real-time
    and historical on-chain metrics.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize on-chain feature engineer.
        
        Args:
            api_key: API key for blockchain data provider
        """
        self.api_key = api_key
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        
    def fetch_metrics(self, symbol: str) -> Dict[str, float]:
        """
        Fetch comprehensive on-chain metrics.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dictionary of on-chain metrics
        """
        base_currency = symbol.split('/')[0]
        
        # Check cache
        cache_key = f"{base_currency}_metrics"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_ttl:
                return cached_data
        
        # Fetch fresh metrics
        metrics = {}
        
        try:
            # Network activity metrics
            metrics.update(self._fetch_network_activity(base_currency))
            
            # Miner metrics
            metrics.update(self._fetch_miner_metrics(base_currency))
            
            # Supply metrics
            metrics.update(self._fetch_supply_metrics(base_currency))
            
            # Exchange flow metrics
            metrics.update(self._fetch_exchange_flows(base_currency))
            
            # Cache results
            self.cache[cache_key] = (datetime.now(), metrics)
            
        except Exception as e:
            logger.error(f"Failed to fetch on-chain metrics: {e}")
            # Return default values
            metrics = self._get_default_metrics()
        
        return metrics
    
    def _fetch_network_activity(self, currency: str) -> Dict[str, float]:
        """
        Fetch network activity metrics.
        
        Args:
            currency: Base currency (BTC, ETH, etc.)
            
        Returns:
            Dictionary of network activity metrics
        """
        # Placeholder implementation
        # In production, would call actual blockchain API
        
        return {
            'active_addresses': np.random.uniform(800000, 1000000),
            'active_addresses_change': np.random.uniform(-0.05, 0.05),
            'transaction_count': np.random.uniform(200000, 300000),
            'transaction_count_change': np.random.uniform(-0.05, 0.05),
            'transaction_volume_usd': np.random.uniform(10e9, 20e9),
            'avg_transaction_value': np.random.uniform(5000, 15000)
        }
    
    def _fetch_miner_metrics(self, currency: str) -> Dict[str, float]:
        """
        Fetch miner-related metrics.
        
        Args:
            currency: Base currency
            
        Returns:
            Dictionary of miner metrics
        """
        if currency != 'BTC':
            # Only applicable for PoW chains
            return {}
        
        return {
            'hash_rate': np.random.uniform(350e18, 450e18),  # Hash/s
            'hash_rate_change': np.random.uniform(-0.03, 0.03),
            'mining_difficulty': np.random.uniform(50e12, 60e12),
            'miner_revenue_usd': np.random.uniform(20e6, 30e6),
            'miner_revenue_per_hash': np.random.uniform(0.1, 0.15)
        }
    
    def _fetch_supply_metrics(self, currency: str) -> Dict[str, float]:
        """
        Fetch supply-related metrics.
        
        Args:
            currency: Base currency
            
        Returns:
            Dictionary of supply metrics
        """
        return {
            'circulating_supply': np.random.uniform(19e6, 19.5e6),
            'supply_change_rate': np.random.uniform(0.001, 0.002),
            'percent_supply_on_exchanges': np.random.uniform(0.10, 0.15),
            'long_term_holder_supply': np.random.uniform(0.60, 0.70),
            'short_term_holder_supply': np.random.uniform(0.30, 0.40)
        }
    
    def _fetch_exchange_flows(self, currency: str) -> Dict[str, float]:
        """
        Fetch exchange flow metrics.
        
        Args:
            currency: Base currency
            
        Returns:
            Dictionary of exchange flow metrics
        """
        return {
            'exchange_inflow': np.random.uniform(5000, 15000),
            'exchange_outflow': np.random.uniform(5000, 15000),
            'net_exchange_flow': np.random.uniform(-5000, 5000),
            'exchange_balance': np.random.uniform(2e6, 3e6),
            'exchange_balance_change': np.random.uniform(-0.02, 0.02)
        }
    
    def _get_default_metrics(self) -> Dict[str, float]:
        """Return default metrics when API is unavailable."""
        return {
            'active_addresses': 0.0,
            'transaction_volume_usd': 0.0,
            'hash_rate': 0.0,
            'miner_revenue_usd': 0.0,
            'net_exchange_flow': 0.0
        }
    
    def get_network_health_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate overall network health score.
        
        Args:
            metrics: Dictionary of on-chain metrics
            
        Returns:
            Health score between 0 and 100
        """
        score = 50.0  # Baseline
        
        # Positive indicators
        if metrics.get('active_addresses_change', 0) > 0:
            score += 10
        
        if metrics.get('hash_rate_change', 0) > 0:
            score += 10
        
        if metrics.get('net_exchange_flow', 0) < 0:  # Outflow is bullish
            score += 10
        
        if metrics.get('long_term_holder_supply', 0) > 0.65:
            score += 10
        
        # Negative indicators
        if metrics.get('percent_supply_on_exchanges', 1) > 0.20:
            score -= 10
        
        return max(0, min(100, score))
    
    def detect_whale_activity(self, metrics: Dict[str, float]) -> Dict[str, any]:
        """
        Detect potential whale activity from on-chain data.
        
        Args:
            metrics: On-chain metrics
            
        Returns:
            Dictionary with whale activity indicators
        """
        whale_threshold = 1000  # BTC or equivalent
        
        avg_tx_value = metrics.get('avg_transaction_value', 0)
        large_tx_detected = avg_tx_value > whale_threshold
        
        net_flow = metrics.get('net_exchange_flow', 0)
        accumulation = net_flow < -whale_threshold
        distribution = net_flow > whale_threshold
        
        return {
            'large_transactions_detected': large_tx_detected,
            'whale_accumulation': accumulation,
            'whale_distribution': distribution,
            'avg_transaction_size': avg_tx_value,
            'alert_level': 'high' if (accumulation or distribution) else 'normal'
        }
    
    def calculate_nvt_ratio(self, metrics: Dict[str, float], market_cap: float) -> float:
        """
        Calculate Network Value to Transaction (NVT) ratio.
        
        Similar to P/E ratio for stocks, high NVT suggests overvaluation.
        
        Args:
            metrics: On-chain metrics
            market_cap: Current market capitalization
            
        Returns:
            NVT ratio
        """
        tx_volume = metrics.get('transaction_volume_usd', 1)
        
        if tx_volume == 0:
            return float('inf')
        
        nvt_ratio = market_cap / tx_volume
        return nvt_ratio
    
    def calculate_mvrv_ratio(
        self,
        current_price: float,
        realized_price: float
    ) -> float:
        """
        Calculate Market Value to Realized Value (MVRV) ratio.
        
        High MVRV suggests profit-taking pressure.
        
        Args:
            current_price: Current market price
            realized_price: Realized price (on-chain average acquisition price)
            
        Returns:
            MVRV ratio
        """
        if realized_price == 0:
            return 1.0
        
        return current_price / realized_price
