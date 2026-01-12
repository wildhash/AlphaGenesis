"""
Continuous Learning Engine - Embodied Learning in Dataflow

Compilation is no longer a phase - it's a background thermodynamic process.

The SDM is always asking:
- "Is this still optimal?"
- "Is this still safe?"
- "Is this still aligned?"

When the answer is "no":
- The graph rewrites itself
- Old paths decay
- New ones strengthen

This is learning - but embodied.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import numpy as np
from loguru import logger


@dataclass
class PerformanceFeedback:
    """Feedback from a trading action."""
    action_id: str
    intent_id: str
    model_type: str
    timestamp: datetime
    success: bool
    pnl: float  # Profit/Loss
    fitness_score: float  # How well it aligned with intent
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy/model."""
    strategy_id: str
    total_actions: int = 0
    successful_actions: int = 0
    total_pnl: float = 0.0
    avg_fitness: float = 0.5
    recent_fitness: deque = field(default_factory=lambda: deque(maxlen=20))
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_actions == 0:
            return 0.5
        return self.successful_actions / self.total_actions

    @property
    def avg_recent_fitness(self) -> float:
        """Calculate average fitness from recent actions."""
        if not self.recent_fitness:
            return self.avg_fitness
        return np.mean(list(self.recent_fitness))

    def update(self, feedback: PerformanceFeedback):
        """Update performance metrics from feedback."""
        self.total_actions += 1
        if feedback.success:
            self.successful_actions += 1

        self.total_pnl += feedback.pnl

        # Update fitness (exponential moving average)
        alpha = 0.1
        self.avg_fitness = alpha * feedback.fitness_score + (1 - alpha) * self.avg_fitness

        # Add to recent fitness
        self.recent_fitness.append(feedback.fitness_score)

        self.last_updated = datetime.now()


class ContinuousLearningEngine:
    """
    Continuous Learning Engine - The System Never Stops Learning.

    This engine:
    1. Collects performance feedback
    2. Identifies what's working and what's not
    3. Adapts strategy selection
    4. Rewrites the intent graph edges
    5. Updates model parameters
    6. Prunes ineffective strategies
    7. Promotes effective ones
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        adaptation_threshold: float = 0.3,
        min_samples: int = 10
    ):
        """
        Initialize continuous learning engine.

        Args:
            learning_rate: How quickly to adapt
            adaptation_threshold: Threshold for triggering adaptation
            min_samples: Minimum samples before adaptation
        """
        self.learning_rate = learning_rate
        self.adaptation_threshold = adaptation_threshold
        self.min_samples = min_samples

        # Performance tracking
        self.feedback_history: List[PerformanceFeedback] = []
        self.strategy_performance: Dict[str, StrategyPerformance] = {}

        # Adaptation history
        self.adaptations: List[Dict[str, Any]] = []

        # State
        self.total_feedback = 0
        self.last_adaptation = datetime.now()

        logger.info("Continuous Learning Engine initialized")

    def record_feedback(self, feedback: PerformanceFeedback):
        """Record feedback from a trading action."""
        self.feedback_history.append(feedback)
        self.total_feedback += 1

        # Update strategy performance
        strategy_id = f"{feedback.intent_id}_{feedback.model_type}"
        if strategy_id not in self.strategy_performance:
            self.strategy_performance[strategy_id] = StrategyPerformance(strategy_id=strategy_id)

        self.strategy_performance[strategy_id].update(feedback)

        logger.debug(
            f"Recorded feedback: {feedback.action_id} - "
            f"Success: {feedback.success}, PnL: {feedback.pnl:.2f}"
        )

    def should_adapt(self) -> bool:
        """Determine if system should adapt based on recent performance."""
        if self.total_feedback < self.min_samples:
            return False

        # Check time since last adaptation
        time_since_adaptation = (datetime.now() - self.last_adaptation).total_seconds()
        if time_since_adaptation < 3600:  # At least 1 hour between adaptations
            return False

        # Check if recent performance is poor
        recent_feedback = self.feedback_history[-self.min_samples:]
        recent_success_rate = sum(1 for f in recent_feedback if f.success) / len(recent_feedback)

        if recent_success_rate < self.adaptation_threshold:
            logger.warning(f"Recent success rate {recent_success_rate:.1%} below threshold, triggering adaptation")
            return True

        return False

    def adapt(self, intent_graph: Any, binding_layer: Any):
        """
        Perform adaptation based on learned performance.

        This is where the system rewrites itself.
        """
        logger.info("="*60)
        logger.info("INITIATING ADAPTATION CYCLE")
        logger.info("="*60)

        adaptations_made = []

        # 1. Identify best and worst performing strategies
        sorted_strategies = sorted(
            self.strategy_performance.values(),
            key=lambda s: s.success_rate,
            reverse=True
        )

        if not sorted_strategies:
            logger.warning("No strategy performance data available")
            return adaptations_made

        best_strategies = sorted_strategies[:3]
        worst_strategies = sorted_strategies[-3:]

        logger.info("Best performing strategies:")
        for s in best_strategies:
            logger.info(f"  {s.strategy_id}: {s.success_rate:.1%} success, PnL: {s.total_pnl:+.2f}")

        logger.info("Worst performing strategies:")
        for s in worst_strategies:
            logger.info(f"  {s.strategy_id}: {s.success_rate:.1%} success, PnL: {s.total_pnl:+.2f}")

        # 2. Adapt intent graph edges
        # Strengthen edges leading to successful strategies
        for strategy in best_strategies:
            if strategy.total_actions < 5:
                continue

            # Parse strategy_id to get intent
            intent_id = strategy.strategy_id.split('_')[0]

            # Find intent node in graph
            if intent_id in intent_graph.nodes:
                node = intent_graph.nodes[intent_id]

                # Increase activation
                node.activation_level = min(1.0, node.activation_level + 0.1)

                # Increase priority
                node.intent.priority = min(10.0, node.intent.priority + 0.5)

                adaptations_made.append({
                    'type': 'boost_intent',
                    'intent_id': intent_id,
                    'reason': f'High success rate: {strategy.success_rate:.1%}'
                })

                logger.info(f"Boosted intent: {intent_id}")

        # Weaken or disable poor strategies
        for strategy in worst_strategies:
            if strategy.total_actions < 5:
                continue

            intent_id = strategy.strategy_id.split('_')[0]

            if intent_id in intent_graph.nodes:
                node = intent_graph.nodes[intent_id]

                # Decrease activation
                node.activation_level = max(0.0, node.activation_level - 0.2)

                # Decrease priority
                node.intent.priority = max(1.0, node.intent.priority - 0.5)

                adaptations_made.append({
                    'type': 'weaken_intent',
                    'intent_id': intent_id,
                    'reason': f'Low success rate: {strategy.success_rate:.1%}'
                })

                logger.info(f"Weakened intent: {intent_id}")

        # 3. Update binding layer with feedback
        binding_feedback = []
        for feedback in self.feedback_history[-50:]:  # Last 50 feedbacks
            binding_feedback.append((
                feedback.intent_id,
                feedback.model_type,
                feedback.success
            ))

        if binding_feedback:
            binding_layer.learn_from_feedback(binding_feedback)
            adaptations_made.append({
                'type': 'update_bindings',
                'samples': len(binding_feedback)
            })

        # 4. Continuous rebinding
        binding_layer.continuous_rebinding()

        # 5. Adapt constraints based on performance
        self._adapt_constraints(intent_graph)

        # Record adaptation
        self.adaptations.append({
            'timestamp': datetime.now(),
            'adaptations': adaptations_made,
            'total_feedback_processed': self.total_feedback
        })

        self.last_adaptation = datetime.now()

        logger.info(f"Adaptation complete: {len(adaptations_made)} changes made")
        logger.info("="*60)

        return adaptations_made

    def _adapt_constraints(self, intent_graph: Any):
        """Adapt intent constraints based on performance."""
        # If we're losing money, tighten risk constraints
        recent_pnl = sum(f.pnl for f in self.feedback_history[-20:])

        if recent_pnl < -50:  # Losing more than $50 recently
            logger.warning(f"Recent PnL: {recent_pnl:.2f}, tightening risk constraints")

            for node in intent_graph.nodes.values():
                for constraint in node.intent.constraints:
                    if constraint.name in ['max_leverage', 'position_size']:
                        # Tighten constraint by 10%
                        constraint.value *= 0.9
                        constraint.penalty *= 1.2
                        logger.info(f"Tightened {constraint.name} to {constraint.value:.2f}")

        # If we're winning, can relax slightly
        elif recent_pnl > 100:  # Winning more than $100
            logger.info(f"Recent PnL: {recent_pnl:.2f}, slightly relaxing constraints")

            for node in intent_graph.nodes.values():
                for constraint in node.intent.constraints:
                    if constraint.name in ['max_leverage']:
                        # Relax by 5% but stay within hackathon limits
                        new_value = min(20.0, constraint.value * 1.05)
                        constraint.value = new_value
                        logger.info(f"Relaxed {constraint.name} to {constraint.value:.2f}")

    def get_adaptation_summary(self) -> Dict[str, Any]:
        """Get summary of adaptation history."""
        return {
            'total_adaptations': len(self.adaptations),
            'total_feedback_processed': self.total_feedback,
            'last_adaptation': self.last_adaptation,
            'strategy_count': len(self.strategy_performance),
            'recent_adaptations': self.adaptations[-5:] if self.adaptations else []
        }

    def get_learning_metrics(self) -> Dict[str, Any]:
        """Get current learning metrics."""
        if not self.feedback_history:
            return {'error': 'No feedback data'}

        recent_feedback = self.feedback_history[-50:]

        return {
            'total_feedback': self.total_feedback,
            'recent_success_rate': sum(1 for f in recent_feedback if f.success) / len(recent_feedback),
            'recent_avg_pnl': np.mean([f.pnl for f in recent_feedback]),
            'recent_avg_fitness': np.mean([f.fitness_score for f in recent_feedback]),
            'total_pnl': sum(f.pnl for f in self.feedback_history),
            'best_strategy': max(
                self.strategy_performance.values(),
                key=lambda s: s.success_rate
            ).strategy_id if self.strategy_performance else None,
            'worst_strategy': min(
                self.strategy_performance.values(),
                key=lambda s: s.success_rate
            ).strategy_id if self.strategy_performance else None,
        }

    def prune_ineffective_strategies(self, min_success_rate: float = 0.2):
        """
        Prune strategies that are consistently ineffective.

        This is like garbage collection for strategies.
        """
        pruned = []

        for strategy_id, performance in list(self.strategy_performance.items()):
            if performance.total_actions < self.min_samples:
                continue

            if performance.success_rate < min_success_rate:
                logger.warning(
                    f"Pruning ineffective strategy: {strategy_id} "
                    f"(success rate: {performance.success_rate:.1%})"
                )
                pruned.append(strategy_id)
                del self.strategy_performance[strategy_id]

        return pruned

    def export_learning_history(self, filepath: str):
        """Export learning history for analysis."""
        import json

        history = {
            'total_feedback': self.total_feedback,
            'adaptations': self.adaptations,
            'strategy_performance': {
                k: {
                    'total_actions': v.total_actions,
                    'successful_actions': v.successful_actions,
                    'success_rate': v.success_rate,
                    'total_pnl': v.total_pnl,
                    'avg_fitness': v.avg_fitness,
                }
                for k, v in self.strategy_performance.items()
            },
            'recent_feedback': [
                {
                    'action_id': f.action_id,
                    'intent_id': f.intent_id,
                    'model_type': f.model_type,
                    'timestamp': f.timestamp.isoformat(),
                    'success': f.success,
                    'pnl': f.pnl,
                    'fitness_score': f.fitness_score,
                }
                for f in self.feedback_history[-100:]
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(history, f, indent=2)

        logger.info(f"Learning history exported to {filepath}")
