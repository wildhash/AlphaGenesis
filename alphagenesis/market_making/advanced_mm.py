"""
Advanced Market Making

Provides liquidity and earns spreads using sophisticated algorithms:
- Avellaneda-Stoikov model
- Inventory risk management
- Dynamic spread optimization
- Order flow prediction
"""

import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class QuoteParameters:
    """Parameters for market making quotes."""
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    spread: float
    reservation_price: float


class AdvancedMarketMaker:
    """
    Provide liquidity and earn spreads using advanced models.
    
    Implements the Avellaneda-Stoikov market making model with
    extensions for inventory management and risk control.
    """
    
    def __init__(
        self,
        risk_aversion: float = 0.1,
        inventory_target: float = 0.0,
        max_inventory: float = 1.0,
        min_spread: float = 0.0005  # 0.05%
    ):
        """
        Initialize advanced market maker.
        
        Args:
            risk_aversion: Risk aversion parameter (gamma)
            inventory_target: Target inventory level
            max_inventory: Maximum allowed inventory
            min_spread: Minimum spread to maintain
        """
        self.risk_aversion = risk_aversion
        self.inventory_target = inventory_target
        self.max_inventory = max_inventory
        self.min_spread = min_spread
        
        self.current_inventory = 0.0
        self.quotes_generated = 0
    
    def calculate_optimal_quotes(
        self,
        order_book: Dict,
        volatility: float,
        time_horizon: float = 1.0
    ) -> QuoteParameters:
        """
        Calculate optimal bid and ask quotes.
        
        Uses Avellaneda-Stoikov model for optimal quote placement.
        
        Args:
            order_book: Current order book data
            volatility: Market volatility (annualized)
            time_horizon: Time horizon for optimization (in days)
            
        Returns:
            Optimal quote parameters
        """
        self.quotes_generated += 1
        
        # Calculate mid price
        mid_price = self._get_mid_price(order_book)
        
        # Calculate reservation price (inventory-adjusted fair price)
        reservation_price = self._calculate_reservation_price(
            mid_price, volatility, time_horizon
        )
        
        # Calculate optimal spread
        optimal_spread = self._calculate_optimal_spread(
            volatility, time_horizon
        )
        
        # Ensure minimum spread
        optimal_spread = max(optimal_spread, self.min_spread)
        
        # Calculate bid and ask prices
        bid_price = reservation_price - optimal_spread / 2
        ask_price = reservation_price + optimal_spread / 2
        
        # Calculate quote sizes
        bid_size, ask_size = self._calculate_quote_sizes(
            order_book, self.current_inventory
        )
        
        return QuoteParameters(
            bid_price=bid_price,
            ask_price=ask_price,
            bid_size=bid_size,
            ask_size=ask_size,
            spread=optimal_spread,
            reservation_price=reservation_price
        )
    
    def _get_mid_price(self, order_book: Dict) -> float:
        """Calculate mid price from order book."""
        if not order_book or not order_book.get('bids') or not order_book.get('asks'):
            return 50000.0  # Default fallback
        
        best_bid = order_book['bids'][0][0]
        best_ask = order_book['asks'][0][0]
        
        return (best_bid + best_ask) / 2
    
    def _calculate_reservation_price(
        self,
        mid_price: float,
        volatility: float,
        time_horizon: float
    ) -> float:
        """
        Calculate reservation price (Avellaneda-Stoikov).
        
        r = s - q * gamma * sigma^2 * T
        
        Where:
        - s = mid price
        - q = inventory
        - gamma = risk aversion
        - sigma = volatility
        - T = time horizon
        """
        inventory_adjustment = (
            self.current_inventory * 
            self.risk_aversion * 
            (volatility ** 2) * 
            time_horizon
        )
        
        reservation_price = mid_price - inventory_adjustment
        
        return reservation_price
    
    def _calculate_optimal_spread(
        self,
        volatility: float,
        time_horizon: float,
        arrival_rate: float = 1.0
    ) -> float:
        """
        Calculate optimal spread (Avellaneda-Stoikov).
        
        delta = gamma * sigma^2 * T + (2/gamma) * ln(1 + gamma/k)
        
        Simplified version: spread proportional to volatility
        """
        # Base spread from volatility
        base_spread = 2 * self.risk_aversion * (volatility ** 2) * time_horizon
        
        # Add market impact component
        market_impact = 0.01 / arrival_rate  # Simplified
        
        total_spread = base_spread + market_impact
        
        return total_spread
    
    def _calculate_quote_sizes(
        self,
        order_book: Dict,
        inventory: float
    ) -> Tuple[float, float]:
        """
        Calculate bid and ask sizes based on inventory.
        
        Args:
            order_book: Current order book
            inventory: Current inventory position
            
        Returns:
            Tuple of (bid_size, ask_size)
        """
        base_size = 0.1  # Base size in BTC
        
        # Adjust sizes based on inventory
        if inventory > 0:
            # Long inventory - increase ask size, decrease bid size
            bid_size = base_size * (1 - min(abs(inventory) / self.max_inventory, 0.8))
            ask_size = base_size * (1 + min(abs(inventory) / self.max_inventory, 0.5))
        elif inventory < 0:
            # Short inventory - increase bid size, decrease ask size
            bid_size = base_size * (1 + min(abs(inventory) / self.max_inventory, 0.5))
            ask_size = base_size * (1 - min(abs(inventory) / self.max_inventory, 0.8))
        else:
            # Neutral inventory - equal sizes
            bid_size = base_size
            ask_size = base_size
        
        return bid_size, ask_size
    
    def update_inventory(self, trade_size: float, side: str):
        """
        Update inventory after a trade.
        
        Args:
            trade_size: Size of trade
            side: Trade side ('buy' or 'sell')
        """
        if side.lower() == 'buy':
            self.current_inventory += trade_size
        elif side.lower() == 'sell':
            self.current_inventory -= trade_size
        
        logger.info(f"Inventory updated: {self.current_inventory:.4f}")
    
    def get_inventory_risk(self) -> Dict[str, float]:
        """
        Calculate inventory risk metrics.
        
        Returns:
            Dictionary of risk metrics
        """
        inventory_pct = self.current_inventory / self.max_inventory if self.max_inventory > 0 else 0
        
        return {
            'current_inventory': self.current_inventory,
            'inventory_pct': inventory_pct,
            'at_risk': abs(inventory_pct) > 0.8,
            'risk_level': abs(inventory_pct)
        }
    
    def should_hedge(self) -> bool:
        """Check if inventory hedging is needed."""
        return abs(self.current_inventory) > self.max_inventory * 0.8
    
    def calculate_hedge_size(self) -> float:
        """Calculate size needed to hedge inventory."""
        target_inventory = self.inventory_target
        hedge_size = self.current_inventory - target_inventory
        
        return hedge_size


class OrderFlowAnalyzer:
    """
    Analyzes order flow for market making optimization.
    """
    
    def __init__(self, lookback_window: int = 100):
        """
        Initialize order flow analyzer.
        
        Args:
            lookback_window: Number of trades to analyze
        """
        self.lookback_window = lookback_window
        self.trade_history = []
    
    def analyze_flow(self, recent_trades: list) -> Dict[str, float]:
        """
        Analyze order flow from recent trades.
        
        Args:
            recent_trades: List of recent trades
            
        Returns:
            Dictionary of flow metrics
        """
        if not recent_trades:
            return self._default_metrics()
        
        # Calculate buy/sell imbalance
        buy_volume = sum(t['size'] for t in recent_trades if t['side'] == 'buy')
        sell_volume = sum(t['size'] for t in recent_trades if t['side'] == 'sell')
        total_volume = buy_volume + sell_volume
        
        if total_volume > 0:
            imbalance = (buy_volume - sell_volume) / total_volume
        else:
            imbalance = 0.0
        
        # Calculate arrival rate
        arrival_rate = len(recent_trades) / max(self.lookback_window, 1)
        
        # Calculate volatility
        prices = [t['price'] for t in recent_trades]
        volatility = np.std(prices) / np.mean(prices) if prices else 0.0
        
        return {
            'buy_sell_imbalance': imbalance,
            'arrival_rate': arrival_rate,
            'volatility': volatility,
            'total_volume': total_volume
        }
    
    def _default_metrics(self) -> Dict[str, float]:
        """Return default metrics when no data available."""
        return {
            'buy_sell_imbalance': 0.0,
            'arrival_rate': 1.0,
            'volatility': 0.01,
            'total_volume': 0.0
        }


class SpreadOptimizer:
    """
    Optimizes spread based on market conditions.
    """
    
    def __init__(self):
        """Initialize spread optimizer."""
        self.performance_history = []
    
    def optimize_spread(
        self,
        base_spread: float,
        fill_rate: float,
        profit_per_fill: float
    ) -> float:
        """
        Optimize spread based on fill rate and profitability.
        
        Args:
            base_spread: Base spread from model
            fill_rate: Recent fill rate (0-1)
            profit_per_fill: Average profit per fill
            
        Returns:
            Optimized spread
        """
        # If fill rate too high, can widen spread
        if fill_rate > 0.8:
            return base_spread * 1.2
        
        # If fill rate too low, tighten spread
        if fill_rate < 0.3:
            return base_spread * 0.8
        
        # Otherwise keep base spread
        return base_spread
