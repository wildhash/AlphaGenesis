"""
Order Book Analyzer

Analyzes order book dynamics to extract microstructure features:
- Bid-ask spread and imbalance
- Order book depth and liquidity
- Large order detection
- Market pressure indicators
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class OrderBookAnalyzer:
    """
    Analyzes order book data for trading signals.
    
    Extracts microstructure features from the order book to
    identify support/resistance levels and market pressure.
    """
    
    def __init__(self, depth_levels: int = 20):
        """
        Initialize order book analyzer.
        
        Args:
            depth_levels: Number of order book levels to analyze
        """
        self.depth_levels = depth_levels
        self.cache = {}
        
    def analyze(self, symbol: str) -> Dict[str, float]:
        """
        Analyze order book for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary of order book metrics
        """
        try:
            # Fetch order book data
            order_book = self._fetch_order_book(symbol)
            
            if order_book is None:
                return self._get_default_metrics()
            
            # Calculate metrics
            metrics = {}
            
            metrics.update(self._calculate_spread(order_book))
            metrics.update(self._calculate_imbalance(order_book))
            metrics.update(self._calculate_depth_metrics(order_book))
            metrics.update(self._detect_large_orders(order_book))
            metrics.update(self._calculate_pressure_indicators(order_book))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze order book: {e}")
            return self._get_default_metrics()
    
    def _fetch_order_book(self, symbol: str) -> Optional[Dict]:
        """
        Fetch order book data.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Order book dictionary or None
        """
        # Placeholder implementation
        # In production, would fetch from exchange API
        
        # Generate synthetic order book for demonstration
        mid_price = 50000.0  # Example mid price
        
        bids = []
        asks = []
        
        for i in range(self.depth_levels):
            # Generate bids (decreasing prices)
            bid_price = mid_price * (1 - 0.0001 * (i + 1))
            bid_size = np.random.uniform(0.1, 5.0)
            bids.append([bid_price, bid_size])
            
            # Generate asks (increasing prices)
            ask_price = mid_price * (1 + 0.0001 * (i + 1))
            ask_size = np.random.uniform(0.1, 5.0)
            asks.append([ask_price, ask_size])
        
        return {
            'bids': bids,  # [[price, size], ...]
            'asks': asks,  # [[price, size], ...]
            'timestamp': None
        }
    
    def _calculate_spread(self, order_book: Dict) -> Dict[str, float]:
        """
        Calculate bid-ask spread metrics.
        
        Args:
            order_book: Order book data
            
        Returns:
            Dictionary with spread metrics
        """
        if not order_book['bids'] or not order_book['asks']:
            return {'bid_ask_spread': 0.0, 'spread_pct': 0.0}
        
        best_bid = order_book['bids'][0][0]
        best_ask = order_book['asks'][0][0]
        
        spread = best_ask - best_bid
        mid_price = (best_bid + best_ask) / 2
        spread_pct = (spread / mid_price) * 100 if mid_price > 0 else 0
        
        return {
            'bid_ask_spread': spread,
            'spread_pct': spread_pct,
            'best_bid': best_bid,
            'best_ask': best_ask,
            'mid_price': mid_price
        }
    
    def _calculate_imbalance(self, order_book: Dict) -> Dict[str, float]:
        """
        Calculate order book imbalance.
        
        Args:
            order_book: Order book data
            
        Returns:
            Dictionary with imbalance metrics
        """
        if not order_book['bids'] or not order_book['asks']:
            return {'order_book_imbalance': 0.0}
        
        # Sum bid and ask volumes
        total_bid_volume = sum(bid[1] for bid in order_book['bids'])
        total_ask_volume = sum(ask[1] for ask in order_book['asks'])
        
        # Calculate imbalance (-1 to +1)
        total_volume = total_bid_volume + total_ask_volume
        if total_volume > 0:
            imbalance = (total_bid_volume - total_ask_volume) / total_volume
        else:
            imbalance = 0.0
        
        return {
            'order_book_imbalance': imbalance,
            'total_bid_volume': total_bid_volume,
            'total_ask_volume': total_ask_volume,
            'bid_ask_volume_ratio': total_bid_volume / total_ask_volume if total_ask_volume > 0 else 1.0
        }
    
    def _calculate_depth_metrics(self, order_book: Dict) -> Dict[str, float]:
        """
        Calculate order book depth metrics.
        
        Args:
            order_book: Order book data
            
        Returns:
            Dictionary with depth metrics
        """
        if not order_book['bids'] or not order_book['asks']:
            return {'depth_ratio': 1.0, 'liquidity_score': 0.0}
        
        # Calculate volume-weighted depth
        bid_depth = sum(
            bid[1] * bid[0] for bid in order_book['bids'][:10]
        )
        ask_depth = sum(
            ask[1] * ask[0] for ask in order_book['asks'][:10]
        )
        
        depth_ratio = bid_depth / ask_depth if ask_depth > 0 else 1.0
        
        # Liquidity score (total volume in top 10 levels)
        total_liquidity = bid_depth + ask_depth
        
        return {
            'depth_ratio': depth_ratio,
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'liquidity_score': total_liquidity
        }
    
    def _detect_large_orders(self, order_book: Dict) -> Dict[str, float]:
        """
        Detect large orders (walls) in the order book.
        
        Args:
            order_book: Order book data
            
        Returns:
            Dictionary with large order indicators
        """
        if not order_book['bids'] or not order_book['asks']:
            return {'large_bid_detected': 0.0, 'large_ask_detected': 0.0}
        
        # Calculate average order size
        avg_bid_size = np.mean([bid[1] for bid in order_book['bids']])
        avg_ask_size = np.mean([ask[1] for ask in order_book['asks']])
        
        # Detect orders larger than 3x average (walls)
        threshold_multiplier = 3.0
        
        large_bids = [
            bid for bid in order_book['bids']
            if bid[1] > avg_bid_size * threshold_multiplier
        ]
        large_asks = [
            ask for ask in order_book['asks']
            if ask[1] > avg_ask_size * threshold_multiplier
        ]
        
        return {
            'large_bid_detected': float(len(large_bids) > 0),
            'large_ask_detected': float(len(large_asks) > 0),
            'large_bid_count': len(large_bids),
            'large_ask_count': len(large_asks),
            'largest_bid_size': max([bid[1] for bid in order_book['bids']]),
            'largest_ask_size': max([ask[1] for ask in order_book['asks']])
        }
    
    def _calculate_pressure_indicators(self, order_book: Dict) -> Dict[str, float]:
        """
        Calculate buying/selling pressure indicators.
        
        Args:
            order_book: Order book data
            
        Returns:
            Dictionary with pressure indicators
        """
        if not order_book['bids'] or not order_book['asks']:
            return {
                'buying_pressure': 0.0,
                'selling_pressure': 0.0,
                'net_pressure': 0.0
            }
        
        # Calculate weighted pressure based on distance from mid price
        mid_price = (order_book['bids'][0][0] + order_book['asks'][0][0]) / 2
        
        buying_pressure = 0.0
        for i, bid in enumerate(order_book['bids'][:10]):
            price, size = bid
            distance = abs(price - mid_price) / mid_price
            weight = 1 / (1 + distance * 100)  # Closer orders have more weight
            buying_pressure += size * weight
        
        selling_pressure = 0.0
        for i, ask in enumerate(order_book['asks'][:10]):
            price, size = ask
            distance = abs(price - mid_price) / mid_price
            weight = 1 / (1 + distance * 100)
            selling_pressure += size * weight
        
        # Net pressure (-1 to +1)
        total_pressure = buying_pressure + selling_pressure
        if total_pressure > 0:
            net_pressure = (buying_pressure - selling_pressure) / total_pressure
        else:
            net_pressure = 0.0
        
        return {
            'buying_pressure': buying_pressure,
            'selling_pressure': selling_pressure,
            'net_pressure': net_pressure,
            'pressure_strength': abs(net_pressure)
        }
    
    def _get_default_metrics(self) -> Dict[str, float]:
        """Return default metrics when order book is unavailable."""
        return {
            'bid_ask_spread': 0.0,
            'order_book_imbalance': 0.0,
            'depth_ratio': 1.0,
            'buying_pressure': 0.0,
            'selling_pressure': 0.0,
            'net_pressure': 0.0
        }
    
    def identify_support_resistance(
        self,
        order_book: Dict,
        num_levels: int = 5
    ) -> Dict[str, List[float]]:
        """
        Identify potential support and resistance levels from order book.
        
        Args:
            order_book: Order book data
            num_levels: Number of levels to identify
            
        Returns:
            Dictionary with support and resistance levels
        """
        if not order_book or not order_book.get('bids') or not order_book.get('asks'):
            return {'support_levels': [], 'resistance_levels': []}
        
        # Sort bids by size (largest first)
        sorted_bids = sorted(
            order_book['bids'],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Sort asks by size (largest first)
        sorted_asks = sorted(
            order_book['asks'],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Extract price levels of largest orders
        support_levels = [bid[0] for bid in sorted_bids[:num_levels]]
        resistance_levels = [ask[0] for ask in sorted_asks[:num_levels]]
        
        return {
            'support_levels': support_levels,
            'resistance_levels': resistance_levels
        }
    
    def calculate_vwap_from_book(self, order_book: Dict) -> Dict[str, float]:
        """
        Calculate Volume-Weighted Average Price from order book.
        
        Args:
            order_book: Order book data
            
        Returns:
            Dictionary with VWAP metrics
        """
        if not order_book or not order_book.get('bids') or not order_book.get('asks'):
            return {'bid_vwap': 0.0, 'ask_vwap': 0.0, 'mid_vwap': 0.0}
        
        # Calculate bid VWAP
        bid_volume = sum(bid[1] for bid in order_book['bids'])
        if bid_volume > 0:
            bid_vwap = sum(
                bid[0] * bid[1] for bid in order_book['bids']
            ) / bid_volume
        else:
            bid_vwap = 0.0
        
        # Calculate ask VWAP
        ask_volume = sum(ask[1] for ask in order_book['asks'])
        if ask_volume > 0:
            ask_vwap = sum(
                ask[0] * ask[1] for ask in order_book['asks']
            ) / ask_volume
        else:
            ask_vwap = 0.0
        
        # Calculate mid VWAP
        mid_vwap = (bid_vwap + ask_vwap) / 2 if (bid_vwap > 0 and ask_vwap > 0) else 0.0
        
        return {
            'bid_vwap': bid_vwap,
            'ask_vwap': ask_vwap,
            'mid_vwap': mid_vwap
        }
