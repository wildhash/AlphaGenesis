"""
Scalper Agent

High-frequency trading agent focused on microstructure patterns:
- Order book imbalances
- Price momentum at tick level
- Short-term mean reversion
"""

import logging
from typing import Dict, Optional
import numpy as np
from alphagenesis.agents.multi_agent_system import AgentDecision, AgentType

logger = logging.getLogger(__name__)


class ScalperAgent:
    """
    Scalper agent for microstructure pattern trading.
    
    Focuses on:
    - Sub-minute price movements
    - Order book imbalances
    - Rapid mean reversion
    - Tick-level momentum
    """
    
    def __init__(
        self,
        target_hold_time: int = 60,  # seconds
        min_spread_pct: float = 0.001,  # 0.1%
        max_position_size: float = 0.05
    ):
        """
        Initialize scalper agent.
        
        Args:
            target_hold_time: Target holding period in seconds
            min_spread_pct: Minimum spread to trade
            max_position_size: Maximum position size
        """
        self.target_hold_time = target_hold_time
        self.min_spread_pct = min_spread_pct
        self.max_position_size = max_position_size
        self.decisions_made = 0
    
    def decide(
        self,
        market_state: Dict,
        historical_data: Optional[Dict] = None
    ) -> AgentDecision:
        """
        Make scalping decision based on microstructure.
        
        Args:
            market_state: Current market state
            historical_data: Optional historical data
            
        Returns:
            Agent decision
        """
        self.decisions_made += 1
        
        # Extract key metrics
        order_book_imbalance = market_state.get('orderbook_order_book_imbalance', 0.0)
        spread_pct = market_state.get('spread_pct', 0.0)
        net_pressure = market_state.get('orderbook_net_pressure', 0.0)
        volatility = market_state.get('volatility', 0.0)
        
        # Calculate scalping signal
        signal, confidence = self._calculate_scalp_signal(
            order_book_imbalance, spread_pct, net_pressure, volatility
        )
        
        # Determine position size
        position_size = self._calculate_position_size(confidence, spread_pct)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            signal, order_book_imbalance, spread_pct, net_pressure
        )
        
        return AgentDecision(
            agent_type=AgentType.SCALPER,
            action=signal,
            confidence=confidence,
            position_size=position_size,
            reasoning=reasoning,
            metadata={
                'target_hold_time': self.target_hold_time,
                'order_book_imbalance': order_book_imbalance,
                'spread_pct': spread_pct
            }
        )
    
    def _calculate_scalp_signal(
        self,
        imbalance: float,
        spread_pct: float,
        pressure: float,
        volatility: float
    ) -> tuple:
        """Calculate scalping signal and confidence."""
        # Check if spread is wide enough to be profitable
        if spread_pct < self.min_spread_pct:
            return 'HOLD', 0.3
        
        # Strong buy signals
        if imbalance > 0.3 and pressure > 0.2:
            confidence = min(0.9, (imbalance + pressure) / 2)
            return 'BUY', confidence
        
        # Strong sell signals
        if imbalance < -0.3 and pressure < -0.2:
            confidence = min(0.9, abs(imbalance + pressure) / 2)
            return 'SELL', confidence
        
        # Moderate signals based on pressure
        if pressure > 0.1:
            return 'BUY', 0.6
        elif pressure < -0.1:
            return 'SELL', 0.6
        
        # Default to hold
        return 'HOLD', 0.5
    
    def _calculate_position_size(
        self,
        confidence: float,
        spread_pct: float
    ) -> float:
        """Calculate position size for scalp."""
        # Base size on confidence
        base_size = confidence * self.max_position_size
        
        # Reduce size if spread is tight
        if spread_pct < self.min_spread_pct * 2:
            base_size *= 0.5
        
        return base_size
    
    def _generate_reasoning(
        self,
        signal: str,
        imbalance: float,
        spread_pct: float,
        pressure: float
    ) -> str:
        """Generate reasoning for decision."""
        reasoning = f"Scalper: {signal}\n"
        reasoning += f"Order book imbalance: {imbalance:+.2%}\n"
        reasoning += f"Spread: {spread_pct:.3%}\n"
        reasoning += f"Net pressure: {pressure:+.2f}\n"
        reasoning += f"Target hold: {self.target_hold_time}s"
        return reasoning
