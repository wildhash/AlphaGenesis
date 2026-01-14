"""
Contextual Bandit Strategy Allocator

Instead of trying to learn a complex policy, we use a bandit to select
which strategy to trust for each (symbol, regime) context.

This is:
- Fast to adapt (online learning)
- Robust (no overfitting)
- Interpretable (you can see which strategies work where)
- Proven in production systems

Strategies compete. Winners get more allocation. Losers get less.
"""
import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from loguru import logger
import time


@dataclass
class StrategyArm:
    """Single strategy arm in the bandit."""
    name: str
    pulls: int = 0  # Number of times selected
    total_reward: float = 0.0  # Sum of rewards
    mean_reward: float = 0.0  # Average reward
    ucb_score: float = 0.0  # Upper confidence bound
    last_pull_time: float = 0.0


class ContextualBanditAllocator:
    """
    Thompson Sampling / UCB bandit for strategy selection.

    Context = (symbol, regime)
    Arms = available strategies
    Reward = realized_pnl - fees - drawdown_penalty

    Each context maintains independent bandit state.
    """

    def __init__(
        self,
        strategies: List[str],
        exploration_rate: float = 0.1,  # Epsilon for epsilon-greedy
        ucb_c: float = 2.0,  # UCB exploration parameter
        algorithm: str = 'ucb',  # 'ucb', 'epsilon_greedy', 'thompson'
        state_path: str = "/tmp/bandit_state.json"
    ):
        self.strategies = strategies
        self.exploration_rate = exploration_rate
        self.ucb_c = ucb_c
        self.algorithm = algorithm
        self.state_path = Path(state_path)

        # State: context -> {strategy -> StrategyArm}
        self.context_arms: Dict[str, Dict[str, StrategyArm]] = {}

        # Global counters
        self.total_pulls = 0
        self.total_reward = 0.0

        self._load_state()

        logger.info(f"BanditAllocator initialized with {len(strategies)} strategies, algorithm={algorithm}")

    def _load_state(self):
        """Load bandit state from disk."""
        if self.state_path.exists():
            try:
                with open(self.state_path, 'r') as f:
                    data = json.load(f)

                for context_key, arms_data in data.get('context_arms', {}).items():
                    self.context_arms[context_key] = {
                        strategy: StrategyArm(**arm_dict)
                        for strategy, arm_dict in arms_data.items()
                    }

                self.total_pulls = data.get('total_pulls', 0)
                self.total_reward = data.get('total_reward', 0.0)

                logger.info(f"Loaded bandit state from {self.state_path}")
            except Exception as e:
                logger.error(f"Failed to load bandit state: {e}")

    def _save_state(self):
        """Persist bandit state to disk."""
        try:
            data = {
                'context_arms': {
                    context: {
                        strategy: asdict(arm)
                        for strategy, arm in arms.items()
                    }
                    for context, arms in self.context_arms.items()
                },
                'total_pulls': self.total_pulls,
                'total_reward': self.total_reward,
                'last_save': time.time()
            }

            # Atomic write
            tmp_path = self.state_path.with_suffix('.tmp')
            with open(tmp_path, 'w') as f:
                json.dump(data, f, indent=2)

            import os
            os.replace(tmp_path, self.state_path)

        except Exception as e:
            logger.error(f"Failed to save bandit state: {e}")

    def _get_context_key(self, symbol: str, regime: str) -> str:
        """Generate context key."""
        return f"{symbol}_{regime}"

    def _init_context(self, context_key: str):
        """Initialize arms for a new context."""
        if context_key not in self.context_arms:
            self.context_arms[context_key] = {
                strategy: StrategyArm(name=strategy)
                for strategy in self.strategies
            }

    def select_strategy(self, symbol: str, regime: str) -> str:
        """
        Select best strategy for given context.

        Returns:
            strategy_name to use
        """
        context_key = self._get_context_key(symbol, regime)
        self._init_context(context_key)

        arms = self.context_arms[context_key]

        if self.algorithm == 'ucb':
            return self._select_ucb(arms)
        elif self.algorithm == 'epsilon_greedy':
            return self._select_epsilon_greedy(arms)
        elif self.algorithm == 'thompson':
            return self._select_thompson(arms)
        else:
            # Fallback: uniform random
            return np.random.choice(self.strategies)

    def _select_ucb(self, arms: Dict[str, StrategyArm]) -> str:
        """Upper Confidence Bound selection."""
        total_context_pulls = sum(arm.pulls for arm in arms.values())

        # Calculate UCB scores
        for strategy, arm in arms.items():
            if arm.pulls == 0:
                # Uninitialized arms get infinite UCB
                arm.ucb_score = float('inf')
            else:
                exploration_bonus = self.ucb_c * np.sqrt(np.log(total_context_pulls + 1) / arm.pulls)
                arm.ucb_score = arm.mean_reward + exploration_bonus

        # Select arm with highest UCB
        best_strategy = max(arms.items(), key=lambda x: x[1].ucb_score)[0]
        return best_strategy

    def _select_epsilon_greedy(self, arms: Dict[str, StrategyArm]) -> str:
        """Epsilon-greedy selection."""
        if np.random.random() < self.exploration_rate:
            # Explore: random strategy
            return np.random.choice(self.strategies)
        else:
            # Exploit: best mean reward
            best_strategy = max(arms.items(), key=lambda x: x[1].mean_reward)[0]
            return best_strategy

    def _select_thompson(self, arms: Dict[str, StrategyArm]) -> str:
        """
        Thompson Sampling (Beta distribution).

        Model rewards as Bernoulli (win/loss), sample from posterior.
        """
        samples = {}

        for strategy, arm in arms.items():
            if arm.pulls == 0:
                # Prior: Beta(1, 1) = uniform
                alpha, beta = 1, 1
            else:
                # Estimate wins/losses from mean_reward
                # Assume reward in [-1, 1], convert to win probability
                win_prob = (arm.mean_reward + 1) / 2  # Map [-1, 1] -> [0, 1]
                wins = int(win_prob * arm.pulls)
                losses = arm.pulls - wins

                alpha = wins + 1
                beta = losses + 1

            # Sample from Beta(alpha, beta)
            sample = np.random.beta(alpha, beta)
            samples[strategy] = sample

        # Select strategy with highest sample
        best_strategy = max(samples.items(), key=lambda x: x[1])[0]
        return best_strategy

    def update(
        self,
        symbol: str,
        regime: str,
        strategy: str,
        reward: float
    ):
        """
        Update bandit with observed reward.

        Reward formula:
            reward = realized_pnl - fees - drawdown_penalty - flip_penalty
        """
        context_key = self._get_context_key(symbol, regime)
        self._init_context(context_key)

        arm = self.context_arms[context_key][strategy]

        # Update arm statistics
        arm.pulls += 1
        arm.total_reward += reward
        arm.mean_reward = arm.total_reward / arm.pulls
        arm.last_pull_time = time.time()

        # Update global counters
        self.total_pulls += 1
        self.total_reward += reward

        logger.info(f"Bandit update: {strategy} in {context_key} | "
                   f"reward={reward:.4f}, mean={arm.mean_reward:.4f}, pulls={arm.pulls}")

        self._save_state()

    def get_best_strategy(self, symbol: str, regime: str) -> Tuple[str, float]:
        """
        Get current best strategy for context (exploitation only).

        Returns:
            (strategy_name, mean_reward)
        """
        context_key = self._get_context_key(symbol, regime)
        self._init_context(context_key)

        arms = self.context_arms[context_key]
        best_strategy = max(arms.items(), key=lambda x: x[1].mean_reward)

        return best_strategy[0], best_strategy[1].mean_reward

    def get_context_stats(self, symbol: str, regime: str) -> Dict:
        """Get statistics for a context."""
        context_key = self._get_context_key(symbol, regime)
        self._init_context(context_key)

        arms = self.context_arms[context_key]

        return {
            'context': context_key,
            'strategies': {
                strategy: {
                    'pulls': arm.pulls,
                    'mean_reward': arm.mean_reward,
                    'total_reward': arm.total_reward,
                    'ucb_score': arm.ucb_score
                }
                for strategy, arm in arms.items()
            },
            'total_pulls': sum(arm.pulls for arm in arms.values())
        }

    def get_global_stats(self) -> Dict:
        """Get global bandit statistics."""
        return {
            'total_pulls': self.total_pulls,
            'total_reward': self.total_reward,
            'avg_reward': self.total_reward / max(1, self.total_pulls),
            'contexts': len(self.context_arms),
            'strategies': len(self.strategies)
        }

    def export_performance_report(self, output_path: str):
        """Export strategy performance report."""
        import csv

        rows = []

        for context_key, arms in self.context_arms.items():
            for strategy, arm in arms.items():
                rows.append({
                    'context': context_key,
                    'strategy': strategy,
                    'pulls': arm.pulls,
                    'mean_reward': arm.mean_reward,
                    'total_reward': arm.total_reward
                })

        with open(output_path, 'w', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        logger.info(f"Exported bandit performance to {output_path}")
