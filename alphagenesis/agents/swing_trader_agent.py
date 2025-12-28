"""
Swing Trader Agent

Medium-term trend following agent:
- Trend detection across multiple timeframes
- Support/resistance levels
- Momentum indicators
"""

import logging
from typing import Dict, Optional
import numpy as np
from alphagenesis.agents.multi_agent_system import AgentDecision, AgentType

logger = logging.getLogger(__name__)


class SwingTraderAgent:
    """
    Swing trader agent for medium-term trends.
    
    Focuses on:
    - Multi-day trend following
    - Key support/resistance levels
    - Momentum confirmation
    - Risk-reward ratios
    """
    
    def __init__(
        self,
        target_hold_days: int = 3,
        min_rr_ratio: float = 2.0,
        max_position_size: float = 0.15
    ):
        """
        Initialize swing trader agent.
        
        Args:
            target_hold_days: Target holding period in days
            min_rr_ratio: Minimum risk-reward ratio
            max_position_size: Maximum position size
        """
        self.target_hold_days = target_hold_days
        self.min_rr_ratio = min_rr_ratio
        self.max_position_size = max_position_size
        self.decisions_made = 0
    
    def decide(
        self,
        market_state: Dict,
        historical_data: Optional[Dict] = None
    ) -> AgentDecision:
        """
        Make swing trading decision.
        
        Args:
            market_state: Current market state
            historical_data: Optional historical data
            
        Returns:
            Agent decision
        """
        self.decisions_made += 1
        
        # Extract trend indicators
        trend = market_state.get('trend', 'neutral')
        momentum = market_state.get('momentum', 0.0)
        rsi = market_state.get('rsi_14', 50)
        macd = market_state.get('macd', 0.0)
        volatility = market_state.get('volatility', 0.0)
        
        # Calculate swing signal
        signal, confidence = self._calculate_swing_signal(
            trend, momentum, rsi, macd
        )
        
        # Determine position size
        position_size = self._calculate_position_size(confidence, volatility)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            signal, trend, momentum, rsi, macd
        )
        
        return AgentDecision(
            agent_type=AgentType.SWING,
            action=signal,
            confidence=confidence,
            position_size=position_size,
            reasoning=reasoning,
            metadata={
                'target_hold_days': self.target_hold_days,
                'trend': trend,
                'rsi': rsi
            }
        )
    
    def _calculate_swing_signal(
        self,
        trend: str,
        momentum: float,
        rsi: float,
        macd: float
    ) -> tuple:
        """Calculate swing trading signal."""
        # Strong uptrend with confirmation
        if trend == 'uptrend' and momentum > 0 and macd > 0:
            if rsi < 70:  # Not overbought
                confidence = min(0.85, 0.7 + momentum * 0.1)
                return 'BUY', confidence
        
        # Strong downtrend with confirmation
        if trend == 'downtrend' and momentum < 0 and macd < 0:
            if rsi > 30:  # Not oversold
                confidence = min(0.85, 0.7 + abs(momentum) * 0.1)
                return 'SELL', confidence
        
        # Oversold bounce opportunity
        if rsi < 30 and momentum > 0:
            return 'BUY', 0.65
        
        # Overbought reversal opportunity
        if rsi > 70 and momentum < 0:
            return 'SELL', 0.65
        
        # Weak signals - hold
        return 'HOLD', 0.4
    
    def _calculate_position_size(
        self,
        confidence: float,
        volatility: float
    ) -> float:
        """Calculate position size."""
        base_size = confidence * self.max_position_size
        
        # Reduce size in high volatility
        if volatility > 0.03:
            base_size *= 0.7
        
        return base_size
    
    def _generate_reasoning(
        self,
        signal: str,
        trend: str,
        momentum: float,
        rsi: float,
        macd: float
    ) -> str:
        """Generate reasoning."""
        reasoning = f"Swing Trader: {signal}\n"
        reasoning += f"Trend: {trend}\n"
        reasoning += f"Momentum: {momentum:+.2f}\n"
        reasoning += f"RSI: {rsi:.1f}\n"
        reasoning += f"MACD: {macd:+.2f}\n"
        reasoning += f"Target hold: {self.target_hold_days} days"
        return reasoning
