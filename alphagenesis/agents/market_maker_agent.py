"""
Market Maker Agent

Provides liquidity and earns spreads:
- Quote generation
- Inventory management
- Spread optimization
"""

import logging
from typing import Dict, Optional
import numpy as np
from alphagenesis.agents.multi_agent_system import AgentDecision, AgentType

logger = logging.getLogger(__name__)


class MarketMakerAgent:
    """
    Market maker agent for liquidity provision.
    
    Focuses on:
    - Two-sided quote generation
    - Inventory risk management
    - Spread capture
    - Order flow analysis
    """
    
    def __init__(
        self,
        target_spread: float = 0.001,  # 0.1%
        max_inventory: float = 0.10
    ):
        """
        Initialize market maker agent.
        
        Args:
            target_spread: Target bid-ask spread
            max_inventory: Maximum inventory position
        """
        self.target_spread = target_spread
        self.max_inventory = max_inventory
        self.current_inventory = 0.0
        self.decisions_made = 0
    
    def decide(
        self,
        market_state: Dict,
        historical_data: Optional[Dict] = None
    ) -> AgentDecision:
        """
        Make market making decision.
        
        Args:
            market_state: Current market state
            historical_data: Optional historical data
            
        Returns:
            Agent decision
        """
        self.decisions_made += 1
        
        # Calculate optimal quotes
        quotes = self._calculate_optimal_quotes(market_state)
        
        # Determine action based on inventory
        signal, confidence, position_size = self._determine_action(quotes)
        
        reasoning = self._generate_reasoning(quotes, self.current_inventory)
        
        return AgentDecision(
            agent_type=AgentType.MARKET_MAKER,
            action=signal,
            confidence=confidence,
            position_size=position_size,
            reasoning=reasoning,
            metadata={
                'bid_quote': quotes['bid'],
                'ask_quote': quotes['ask'],
                'inventory': self.current_inventory
            }
        )
    
    def _calculate_optimal_quotes(self, market_state: Dict) -> Dict:
        """Calculate optimal bid and ask quotes."""
        mid_price = market_state.get('mid_price', market_state.get('close', 0))
        volatility = market_state.get('volatility', 0.01)
        
        # Avellaneda-Stoikov inspired spread
        optimal_spread = self.target_spread + volatility * 2
        
        bid = mid_price * (1 - optimal_spread / 2)
        ask = mid_price * (1 + optimal_spread / 2)
        
        # Adjust for inventory
        if self.current_inventory > 0:
            # Long inventory - widen bid, tighten ask
            bid *= 0.999
            ask *= 0.9995
        elif self.current_inventory < 0:
            # Short inventory - tighten bid, widen ask
            bid *= 0.9995
            ask *= 1.001
        
        return {
            'bid': bid,
            'ask': ask,
            'spread': optimal_spread,
            'mid': mid_price
        }
    
    def _determine_action(self, quotes: Dict) -> tuple:
        """Determine trading action based on inventory."""
        # Market makers typically hold for spread capture
        # Action based on inventory management
        
        if abs(self.current_inventory) > self.max_inventory * 0.8:
            # Need to reduce inventory
            if self.current_inventory > 0:
                return 'SELL', 0.7, min(0.05, abs(self.current_inventory))
            else:
                return 'BUY', 0.7, min(0.05, abs(self.current_inventory))
        
        # Normal market making - hold and provide liquidity
        return 'HOLD', 0.8, 0.0
    
    def _generate_reasoning(self, quotes: Dict, inventory: float) -> str:
        """Generate reasoning."""
        reasoning = f"Market Maker: Providing liquidity\n"
        reasoning += f"Bid: {quotes['bid']:.2f}\n"
        reasoning += f"Ask: {quotes['ask']:.2f}\n"
        reasoning += f"Spread: {quotes['spread']:.3%}\n"
        reasoning += f"Inventory: {inventory:+.2%}"
        return reasoning
