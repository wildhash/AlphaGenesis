"""
Multi-Agent Trading System

Coordinates multiple specialized trading agents:
- Scalper Agent: Microstructure patterns
- Swing Trader Agent: Medium-term trends
- Arbitrage Agent: Cross-exchange opportunities
- Market Maker Agent: Liquidity provision
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of trading agents."""
    SCALPER = "scalper"
    SWING = "swing"
    ARBITRAGE = "arbitrage"
    MARKET_MAKER = "market_maker"


@dataclass
class AgentDecision:
    """Trading decision from an agent."""
    agent_type: AgentType
    action: str  # BUY, SELL, HOLD
    confidence: float
    position_size: float
    reasoning: str
    metadata: Dict


@dataclass
class ConsensusDecision:
    """Final consensus decision from all agents."""
    action: str
    confidence: float
    position_size: float
    participating_agents: List[AgentType]
    reasoning: str
    agent_votes: Dict[str, AgentDecision]


class MultiAgentTradingSystem:
    """
    Multiple specialized agents working together.
    
    Each agent specializes in a different trading strategy:
    - Scalper: High-frequency microstructure patterns
    - Swing: Medium-term trend following
    - Arbitrage: Price discrepancies across markets
    - Market Maker: Providing liquidity for spreads
    
    A coordinator aggregates their decisions using consensus mechanisms.
    """
    
    def __init__(
        self,
        enable_scalper: bool = True,
        enable_swing: bool = True,
        enable_arbitrage: bool = True,
        enable_market_maker: bool = False
    ):
        """
        Initialize multi-agent system.
        
        Args:
            enable_scalper: Enable scalper agent
            enable_swing: Enable swing trader agent
            enable_arbitrage: Enable arbitrage agent
            enable_market_maker: Enable market maker agent
        """
        self.agents = {}
        self._initialize_agents(
            enable_scalper, enable_swing, enable_arbitrage, enable_market_maker
        )
        
        self.coordinator = AgentCoordinator()
        self.consensus_mechanism = ConsensusMechanism()
        
        logger.info(f"Initialized multi-agent system with {len(self.agents)} agents")
    
    def _initialize_agents(
        self,
        enable_scalper: bool,
        enable_swing: bool,
        enable_arbitrage: bool,
        enable_market_maker: bool
    ):
        """Initialize enabled agents."""
        if enable_scalper:
            try:
                from alphagenesis.agents.scalper_agent import ScalperAgent
                self.agents['scalper'] = ScalperAgent()
                logger.info("Scalper agent initialized")
            except ImportError:
                logger.warning("Scalper agent not available")
        
        if enable_swing:
            try:
                from alphagenesis.agents.swing_trader_agent import SwingTraderAgent
                self.agents['swing'] = SwingTraderAgent()
                logger.info("Swing trader agent initialized")
            except ImportError:
                logger.warning("Swing trader agent not available")
        
        if enable_arbitrage:
            try:
                from alphagenesis.agents.arbitrage_agent import ArbitrageAgent
                self.agents['arbitrage'] = ArbitrageAgent()
                logger.info("Arbitrage agent initialized")
            except ImportError:
                logger.warning("Arbitrage agent not available")
        
        if enable_market_maker:
            try:
                from alphagenesis.agents.market_maker_agent import MarketMakerAgent
                self.agents['market_maker'] = MarketMakerAgent()
                logger.info("Market maker agent initialized")
            except ImportError:
                logger.warning("Market maker agent not available")
    
    def decide(
        self,
        market_state: Dict,
        historical_data: Optional[Dict] = None
    ) -> ConsensusDecision:
        """
        Make trading decision using all agents.
        
        Args:
            market_state: Current market state dictionary
            historical_data: Optional historical data
            
        Returns:
            Consensus decision from all agents
        """
        # Step 1: Collect decisions from all agents
        agent_decisions = {}
        for name, agent in self.agents.items():
            try:
                decision = agent.decide(market_state, historical_data)
                agent_decisions[name] = decision
                logger.debug(f"{name} agent decision: {decision.action} (confidence: {decision.confidence:.2f})")
            except Exception as e:
                logger.error(f"Error getting decision from {name} agent: {e}")
        
        # Step 2: Reach consensus
        if agent_decisions:
            final_decision = self.consensus_mechanism.reach_consensus(agent_decisions)
        else:
            # No agents available - return HOLD
            final_decision = ConsensusDecision(
                action='HOLD',
                confidence=0.0,
                position_size=0.0,
                participating_agents=[],
                reasoning="No agents available for decision",
                agent_votes={}
            )
        
        # Step 3: Apply risk constraints
        risk_adjusted_decision = self.coordinator.apply_risk_constraints(
            final_decision, market_state
        )
        
        return risk_adjusted_decision
    
    def get_agent_status(self) -> Dict[str, Dict]:
        """Get status of all agents."""
        status = {}
        for name, agent in self.agents.items():
            status[name] = {
                'enabled': True,
                'type': type(agent).__name__,
                'decisions_made': getattr(agent, 'decisions_made', 0)
            }
        return status


class AgentCoordinator:
    """
    Coordinates agent activities and applies system-wide constraints.
    """
    
    def __init__(
        self,
        max_position_size: float = 0.10,
        max_leverage: float = 3.0
    ):
        """
        Initialize coordinator.
        
        Args:
            max_position_size: Maximum position size (fraction of capital)
            max_leverage: Maximum leverage allowed
        """
        self.max_position_size = max_position_size
        self.max_leverage = max_leverage
    
    def apply_risk_constraints(
        self,
        decision: ConsensusDecision,
        market_state: Dict
    ) -> ConsensusDecision:
        """
        Apply risk management constraints to decision.
        
        Args:
            decision: Raw consensus decision
            market_state: Current market state
            
        Returns:
            Risk-adjusted decision
        """
        adjusted = decision
        
        # Limit position size
        if decision.position_size > self.max_position_size:
            adjusted.position_size = self.max_position_size
            adjusted.reasoning += f" | Position size limited to {self.max_position_size:.1%}"
        
        # Check volatility
        volatility = market_state.get('volatility', 0.0)
        if volatility > 0.05:  # 5% daily volatility
            adjusted.position_size *= 0.5
            adjusted.reasoning += f" | Reduced size due to high volatility ({volatility:.1%})"
        
        # Ensure action is valid
        if adjusted.action not in ['BUY', 'SELL', 'HOLD']:
            adjusted.action = 'HOLD'
            adjusted.confidence = 0.0
            adjusted.reasoning = "Invalid action - defaulting to HOLD"
        
        return adjusted


class ConsensusMechanism:
    """
    Reaches consensus among multiple agents.
    
    Uses weighted voting based on agent confidence and historical performance.
    """
    
    def __init__(self, method: str = 'weighted_vote'):
        """
        Initialize consensus mechanism.
        
        Args:
            method: Consensus method ('weighted_vote', 'majority', 'average')
        """
        self.method = method
        self.agent_weights = {}  # Historical performance weights
    
    def reach_consensus(
        self,
        agent_decisions: Dict[str, AgentDecision]
    ) -> ConsensusDecision:
        """
        Reach consensus from agent decisions.
        
        Args:
            agent_decisions: Dictionary of agent decisions
            
        Returns:
            Consensus decision
        """
        if not agent_decisions:
            return self._default_decision()
        
        if self.method == 'weighted_vote':
            return self._weighted_vote(agent_decisions)
        elif self.method == 'majority':
            return self._majority_vote(agent_decisions)
        elif self.method == 'average':
            return self._average_consensus(agent_decisions)
        else:
            return self._weighted_vote(agent_decisions)
    
    def _weighted_vote(
        self,
        agent_decisions: Dict[str, AgentDecision]
    ) -> ConsensusDecision:
        """Weighted voting based on confidence."""
        # Calculate weighted scores for each action
        action_scores = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
        total_weight = 0.0
        total_position_size = 0.0
        
        for agent_name, decision in agent_decisions.items():
            weight = decision.confidence * self._get_agent_weight(agent_name)
            action_scores[decision.action] += weight
            total_weight += weight
            total_position_size += decision.position_size * weight
        
        # Determine winning action
        if total_weight > 0:
            final_action = max(action_scores, key=action_scores.get)
            final_confidence = action_scores[final_action] / total_weight
            final_position_size = total_position_size / total_weight
        else:
            final_action = 'HOLD'
            final_confidence = 0.0
            final_position_size = 0.0
        
        # Generate reasoning
        reasoning = self._generate_consensus_reasoning(
            agent_decisions, final_action, action_scores
        )
        
        participating_agents = [
            AgentType(decision.agent_type.value)
            for decision in agent_decisions.values()
        ]
        
        return ConsensusDecision(
            action=final_action,
            confidence=final_confidence,
            position_size=final_position_size,
            participating_agents=participating_agents,
            reasoning=reasoning,
            agent_votes=agent_decisions
        )
    
    def _majority_vote(
        self,
        agent_decisions: Dict[str, AgentDecision]
    ) -> ConsensusDecision:
        """Simple majority voting."""
        action_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        
        for decision in agent_decisions.values():
            action_counts[decision.action] += 1
        
        final_action = max(action_counts, key=action_counts.get)
        final_confidence = action_counts[final_action] / len(agent_decisions)
        
        # Average position size from agreeing agents
        agreeing_sizes = [
            d.position_size for d in agent_decisions.values()
            if d.action == final_action
        ]
        final_position_size = np.mean(agreeing_sizes) if agreeing_sizes else 0.0
        
        reasoning = f"Majority vote: {action_counts[final_action]}/{len(agent_decisions)} agents"
        
        return ConsensusDecision(
            action=final_action,
            confidence=final_confidence,
            position_size=final_position_size,
            participating_agents=[d.agent_type for d in agent_decisions.values()],
            reasoning=reasoning,
            agent_votes=agent_decisions
        )
    
    def _average_consensus(
        self,
        agent_decisions: Dict[str, AgentDecision]
    ) -> ConsensusDecision:
        """Average consensus across all agents."""
        # Convert actions to numeric: BUY=1, HOLD=0, SELL=-1
        action_map = {'BUY': 1, 'HOLD': 0, 'SELL': -1}
        
        avg_action_value = np.mean([
            action_map[d.action] * d.confidence
            for d in agent_decisions.values()
        ])
        
        # Convert back to action
        if avg_action_value > 0.3:
            final_action = 'BUY'
        elif avg_action_value < -0.3:
            final_action = 'SELL'
        else:
            final_action = 'HOLD'
        
        final_confidence = abs(avg_action_value)
        final_position_size = np.mean([d.position_size for d in agent_decisions.values()])
        
        reasoning = f"Average consensus: {avg_action_value:.2f}"
        
        return ConsensusDecision(
            action=final_action,
            confidence=final_confidence,
            position_size=final_position_size,
            participating_agents=[d.agent_type for d in agent_decisions.values()],
            reasoning=reasoning,
            agent_votes=agent_decisions
        )
    
    def _get_agent_weight(self, agent_name: str) -> float:
        """Get performance-based weight for agent."""
        return self.agent_weights.get(agent_name, 1.0)
    
    def update_agent_weights(self, performance: Dict[str, float]):
        """Update agent weights based on performance."""
        self.agent_weights.update(performance)
    
    def _generate_consensus_reasoning(
        self,
        decisions: Dict[str, AgentDecision],
        final_action: str,
        action_scores: Dict[str, float]
    ) -> str:
        """Generate reasoning for consensus."""
        reasoning = f"Consensus: {final_action}\n"
        reasoning += "Agent votes:\n"
        
        for agent_name, decision in decisions.items():
            agreement = "✓" if decision.action == final_action else "✗"
            reasoning += f"  {agreement} {agent_name}: {decision.action} ({decision.confidence:.0%})\n"
        
        reasoning += f"Score distribution: "
        reasoning += ", ".join([f"{k}={v:.2f}" for k, v in action_scores.items()])
        
        return reasoning
    
    def _default_decision(self) -> ConsensusDecision:
        """Return default HOLD decision."""
        return ConsensusDecision(
            action='HOLD',
            confidence=0.0,
            position_size=0.0,
            participating_agents=[],
            reasoning="No agent decisions available",
            agent_votes={}
        )
