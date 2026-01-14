"""
Intent Graph - The True "Program" of the SDM

Instead of instructions, we have Intents.
Instead of control flow, we have dataflow between Intent nodes.
The graph is alive, mutable, and self-healing.

Intent = (Goal, Constraints, Stakes, Context, Confidence Threshold)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Set
import numpy as np
from datetime import datetime
from loguru import logger


class IntentType(Enum):
    """Types of intents in the trading system."""
    MAXIMIZE_RETURNS = "maximize_returns"
    MINIMIZE_RISK = "minimize_risk"
    MAINTAIN_LIQUIDITY = "maintain_liquidity"
    PRESERVE_CAPITAL = "preserve_capital"
    EXPLOIT_OPPORTUNITY = "exploit_opportunity"
    HEDGE_EXPOSURE = "hedge_exposure"


class ConstraintType(Enum):
    """Types of constraints."""
    HARD = "hard"  # Must never be violated
    SOFT = "soft"  # Prefer not to violate
    ADAPTIVE = "adaptive"  # Adjusts based on conditions


@dataclass
class Constraint:
    """A constraint on an intent."""
    name: str
    constraint_type: ConstraintType
    value: float
    penalty: float  # Asymmetric penalty for violation
    description: str

    def evaluate(self, current_value: float) -> float:
        """
        Evaluate constraint violation.

        Returns:
            Penalty value (0 if satisfied, >0 if violated)
        """
        if current_value > self.value:
            violation = current_value - self.value
            return violation * self.penalty
        return 0.0

    def is_violated(self, current_value: float) -> bool:
        """Check if constraint is violated."""
        return current_value > self.value


@dataclass
class Stake:
    """Stakes associated with an intent - what's at risk."""
    capital_at_risk: float  # Amount of capital
    max_loss_acceptable: float  # Maximum acceptable loss
    time_horizon: int  # Time horizon in seconds
    reputation_score: float  # Reputation/confidence stake


@dataclass
class Intent:
    """
    Core Intent primitive.

    Intent is not code. Intent is not a string.
    Intent = (Goal, Constraints, Stakes, Context, Confidence Threshold)
    """
    goal: str  # High-level goal description
    goal_type: IntentType
    constraints: List[Constraint] = field(default_factory=list)
    stakes: Optional[Stake] = None
    context: Dict[str, Any] = field(default_factory=dict)
    confidence_threshold: float = 0.7
    priority: float = 1.0  # Higher = more important
    created_at: datetime = field(default_factory=datetime.now)

    def evaluate_fitness(self, proposed_action: Dict) -> float:
        """
        Evaluate how well a proposed action satisfies this intent.

        Returns:
            Fitness score [0, 1] where 1 is perfect alignment
        """
        # Calculate constraint satisfaction
        constraint_penalty = sum(
            c.evaluate(proposed_action.get(c.name, 0))
            for c in self.constraints
        )

        # Base fitness from confidence
        base_fitness = proposed_action.get('confidence', 0.5)

        # Apply constraint penalties
        fitness = base_fitness - constraint_penalty

        # Ensure in [0, 1]
        return max(0.0, min(1.0, fitness))

    def can_proceed(self, fitness: float) -> bool:
        """Check if action meets confidence threshold."""
        return fitness >= self.confidence_threshold


class EdgeType(Enum):
    """Types of edges in the intent graph."""
    DEPENDENCY = "dependency"  # A depends on B
    TRADEOFF = "tradeoff"  # A vs B tradeoff
    INHIBITION = "inhibition"  # A inhibits B
    FEEDBACK = "feedback"  # A provides feedback to B
    ENHANCEMENT = "enhancement"  # A enhances B


@dataclass
class IntentEdge:
    """Edge connecting two intent nodes."""
    from_node: str  # Node ID
    to_node: str  # Node ID
    edge_type: EdgeType
    weight: float  # Strength of relationship
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentNode:
    """
    Node in the Intent Graph.

    Contains an intent and its execution state.
    """
    node_id: str
    intent: Intent
    is_active: bool = True
    activation_level: float = 0.0  # [0, 1] - how "pressured" is this intent
    last_fitness: float = 0.0
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate of this intent."""
        if self.execution_count == 0:
            return 0.5  # Neutral prior
        return self.success_count / self.execution_count

    def activate(self, pressure: float):
        """Increase activation level by pressure."""
        self.activation_level = min(1.0, self.activation_level + pressure)

    def decay(self, rate: float = 0.1):
        """Decay activation over time."""
        self.activation_level = max(0.0, self.activation_level - rate)

    def record_execution(self, success: bool, fitness: float):
        """Record execution result."""
        self.execution_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.last_fitness = fitness


class IntentGraph:
    """
    The Intent Graph - The True "Program".

    No main(). No entry point. No termination.
    Just continuous pressure gradients in meaning space.
    """

    def __init__(self):
        """Initialize empty intent graph."""
        self.nodes: Dict[str, IntentNode] = {}
        self.edges: List[IntentEdge] = []
        self.time_step = 0
        logger.info("Intent Graph initialized")

    def add_intent(
        self,
        node_id: str,
        intent: Intent,
        activate: bool = True
    ) -> IntentNode:
        """Add an intent node to the graph."""
        node = IntentNode(
            node_id=node_id,
            intent=intent,
            is_active=activate,
            activation_level=1.0 if activate else 0.0
        )
        self.nodes[node_id] = node
        logger.info(f"Added intent node: {node_id} - {intent.goal}")
        return node

    def add_edge(
        self,
        from_node: str,
        to_node: str,
        edge_type: EdgeType,
        weight: float = 1.0
    ):
        """Add an edge between intents."""
        edge = IntentEdge(
            from_node=from_node,
            to_node=to_node,
            edge_type=edge_type,
            weight=weight
        )
        self.edges.append(edge)
        logger.debug(f"Added edge: {from_node} -> {to_node} ({edge_type.value})")

    def propagate_activation(self):
        """
        Propagate activation through the graph.

        This is the dataflow: pressure propagates based on edge types.
        """
        for edge in self.edges:
            from_node = self.nodes.get(edge.from_node)
            to_node = self.nodes.get(edge.to_node)

            if not from_node or not to_node:
                continue

            if not from_node.is_active:
                continue

            # Propagate based on edge type
            if edge.edge_type == EdgeType.DEPENDENCY:
                # If A is active, B should activate
                pressure = from_node.activation_level * edge.weight
                to_node.activate(pressure)

            elif edge.edge_type == EdgeType.INHIBITION:
                # If A is active, B should deactivate
                inhibition = from_node.activation_level * edge.weight
                to_node.activation_level = max(0.0, to_node.activation_level - inhibition)

            elif edge.edge_type == EdgeType.TRADEOFF:
                # A and B compete for activation
                if from_node.activation_level > to_node.activation_level:
                    transfer = (from_node.activation_level - to_node.activation_level) * edge.weight * 0.1
                    from_node.activation_level -= transfer
                    to_node.activation_level += transfer

            elif edge.edge_type == EdgeType.FEEDBACK:
                # Use historical success to modulate activation
                feedback_signal = from_node.success_rate * edge.weight
                to_node.activate(feedback_signal * 0.1)

            elif edge.edge_type == EdgeType.ENHANCEMENT:
                # If both active, amplify
                if to_node.activation_level > 0:
                    enhancement = from_node.activation_level * edge.weight * 0.1
                    to_node.activate(enhancement)

    def decay_all(self, rate: float = 0.05):
        """Decay all activation levels over time."""
        for node in self.nodes.values():
            node.decay(rate)

    def get_most_active_intents(self, top_k: int = 3) -> List[IntentNode]:
        """Get the most active intent nodes."""
        active_nodes = [n for n in self.nodes.values() if n.is_active]
        sorted_nodes = sorted(active_nodes, key=lambda n: n.activation_level, reverse=True)
        return sorted_nodes[:top_k]

    def evaluate_proposed_action(self, action: Dict) -> Dict[str, float]:
        """
        Evaluate a proposed action against all active intents.

        Returns:
            Fitness scores for each intent
        """
        fitness_scores = {}
        for node_id, node in self.nodes.items():
            if not node.is_active:
                continue
            fitness = node.intent.evaluate_fitness(action)
            fitness_scores[node_id] = fitness
        return fitness_scores

    def should_execute_action(self, action: Dict) -> tuple[bool, str]:
        """
        Determine if an action should be executed based on intent graph.

        Returns:
            (should_execute, reasoning)
        """
        fitness_scores = self.evaluate_proposed_action(action)

        # Weighted average fitness by priority and activation
        weighted_fitness = 0.0
        total_weight = 0.0

        for node_id, fitness in fitness_scores.items():
            node = self.nodes[node_id]
            weight = node.intent.priority * node.activation_level
            weighted_fitness += fitness * weight
            total_weight += weight

        if total_weight == 0:
            return False, "No active intents"

        avg_fitness = weighted_fitness / total_weight

        # Check if most active intents can proceed
        active_intents = self.get_most_active_intents()

        for node in active_intents:
            fitness = fitness_scores.get(node.node_id, 0.0)
            if not node.intent.can_proceed(fitness):
                return False, f"Intent '{node.intent.goal}' fitness {fitness:.2f} below threshold {node.intent.confidence_threshold}"

        return True, f"Weighted fitness {avg_fitness:.2f} satisfies all active intents"

    def record_action_result(
        self,
        action: Dict,
        success: bool,
        fitness_scores: Optional[Dict[str, float]] = None
    ):
        """Record the result of an executed action."""
        if fitness_scores is None:
            fitness_scores = self.evaluate_proposed_action(action)

        for node_id, fitness in fitness_scores.items():
            node = self.nodes.get(node_id)
            if node and node.is_active:
                node.record_execution(success, fitness)

    def step(self):
        """
        Advance the intent graph one time step.

        1. Propagate activation
        2. Decay old activation
        3. Increment time
        """
        self.time_step += 1
        self.propagate_activation()
        self.decay_all()

    def get_state_summary(self) -> Dict[str, Any]:
        """Get current state of the intent graph."""
        return {
            'time_step': self.time_step,
            'active_nodes': len([n for n in self.nodes.values() if n.is_active]),
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'most_active': [
                {
                    'node_id': n.node_id,
                    'goal': n.intent.goal,
                    'activation': n.activation_level,
                    'success_rate': n.success_rate
                }
                for n in self.get_most_active_intents()
            ]
        }

    def initialize_trading_intents(self):
        """
        Initialize the graph with standard trading intents.

        This creates the foundational intent structure for trading.
        """
        # Primary intent: Grow capital
        grow_capital = Intent(
            goal="Grow capital aggressively without catastrophic drawdown",
            goal_type=IntentType.MAXIMIZE_RETURNS,
            constraints=[
                Constraint(
                    name="max_drawdown",
                    constraint_type=ConstraintType.HARD,
                    value=0.25,  # 25% max drawdown
                    penalty=100.0,
                    description="Never lose more than 25% of capital"
                ),
                Constraint(
                    name="max_leverage",
                    constraint_type=ConstraintType.HARD,
                    value=20.0,  # Hackathon limit
                    penalty=1000.0,
                    description="Never exceed 20x leverage"
                ),
            ],
            stakes=Stake(
                capital_at_risk=1000.0,
                max_loss_acceptable=250.0,
                time_horizon=21 * 24 * 3600,  # 21 days
                reputation_score=1.0
            ),
            confidence_threshold=0.1,  # LOWERED for competition - let signals through!
            priority=10.0
        )

        # Risk management intent
        manage_risk = Intent(
            goal="Protect capital from adverse moves",
            goal_type=IntentType.MINIMIZE_RISK,
            constraints=[
                Constraint(
                    name="daily_drawdown",
                    constraint_type=ConstraintType.HARD,
                    value=0.10,  # 10% daily
                    penalty=50.0,
                    description="Daily loss limit"
                ),
                Constraint(
                    name="position_size",
                    constraint_type=ConstraintType.SOFT,
                    value=0.30,  # 30% max per position
                    penalty=10.0,
                    description="Position size limit"
                ),
            ],
            confidence_threshold=0.1,  # LOWERED for competition
            priority=9.0
        )

        # Opportunity exploitation
        exploit_opportunities = Intent(
            goal="Capitalize on high-confidence market opportunities",
            goal_type=IntentType.EXPLOIT_OPPORTUNITY,
            constraints=[
                Constraint(
                    name="min_confidence",
                    constraint_type=ConstraintType.SOFT,
                    value=0.1,  # LOWERED for competition - allow more trades
                    penalty=1.0,  # Reduced penalty from 5.0 to 1.0
                    description="Minimum signal confidence"
                ),
                Constraint(
                    name="min_risk_reward",
                    constraint_type=ConstraintType.SOFT,
                    value=3.0,
                    penalty=3.0,
                    description="Minimum risk-reward ratio"
                ),
            ],
            confidence_threshold=0.1,  # LOWERED for competition
            priority=7.0
        )

        # Liquidity maintenance
        maintain_liquidity = Intent(
            goal="Maintain sufficient liquidity for opportunities",
            goal_type=IntentType.MAINTAIN_LIQUIDITY,
            constraints=[
                Constraint(
                    name="min_cash_reserve",
                    constraint_type=ConstraintType.SOFT,
                    value=0.20,  # 20% in cash
                    penalty=2.0,
                    description="Keep cash reserve"
                ),
            ],
            confidence_threshold=0.1,  # LOWERED for competition
            priority=5.0
        )

        # Add nodes
        self.add_intent("grow_capital", grow_capital, activate=True)
        self.add_intent("manage_risk", manage_risk, activate=True)
        self.add_intent("exploit_opportunities", exploit_opportunities, activate=True)
        self.add_intent("maintain_liquidity", maintain_liquidity, activate=True)

        # Add edges - define relationships
        # Growing capital depends on exploiting opportunities
        self.add_edge("exploit_opportunities", "grow_capital", EdgeType.DEPENDENCY, weight=0.8)

        # Risk management inhibits aggressive growth
        self.add_edge("manage_risk", "grow_capital", EdgeType.TRADEOFF, weight=0.5)

        # Risk management provides feedback to opportunity exploitation
        self.add_edge("manage_risk", "exploit_opportunities", EdgeType.FEEDBACK, weight=0.7)

        # Liquidity maintenance enhances opportunity exploitation
        self.add_edge("maintain_liquidity", "exploit_opportunities", EdgeType.ENHANCEMENT, weight=0.6)

        # Opportunity exploitation inhibits pure risk avoidance
        self.add_edge("exploit_opportunities", "manage_risk", EdgeType.INHIBITION, weight=0.3)

        logger.info("Trading intent graph initialized with 4 primary intents")
