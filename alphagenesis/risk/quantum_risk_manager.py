"""
Quantum Risk Manager

Risk management inspired by quantum probability theory.
Uses quantum superposition concepts for position sizing and risk assessment.
"""

import numpy as np
import logging
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MarketState(Enum):
    """Market state classifications."""
    BULL = "bull"
    BEAR = "bear"
    NEUTRAL = "neutral"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class PositionRecommendation:
    """Position sizing recommendation with quantum-inspired calculations."""
    size: float  # Position size as fraction of capital
    stop_loss: float  # Stop loss price
    take_profit: float  # Take profit price
    uncertainty: float  # Uncertainty score (0-1)
    confidence: float  # Confidence in recommendation (0-1)
    reasoning: str  # Explanation of recommendation
    quantum_state: Dict[str, float]  # Probability amplitudes


class QuantumRiskManager:
    """
    Risk management inspired by quantum probability theory.
    
    Uses concepts from quantum mechanics:
    - Superposition: Multiple market states exist simultaneously
    - Wave function collapse: Observation resolves to classical state
    - Uncertainty principle: Trade-off between precision and timing
    """
    
    def __init__(
        self,
        initial_capital: float = 10000,
        max_risk_per_trade: float = 0.02,
        max_total_risk: float = 0.10,
        risk_free_rate: float = 0.0
    ):
        """
        Initialize quantum risk manager.
        
        Args:
            initial_capital: Starting capital
            max_risk_per_trade: Maximum risk per trade (fraction)
            max_total_risk: Maximum total portfolio risk (fraction)
            risk_free_rate: Risk-free rate for calculations
        """
        self.capital = initial_capital
        self.max_risk_per_trade = max_risk_per_trade
        self.max_total_risk = max_total_risk
        self.risk_free_rate = risk_free_rate
        
        # Quantum state tracking
        self.market_state_history = []
        self.position_history = []
    
    def calculate_position_size(
        self,
        signal_confidence: float,
        current_price: float,
        volatility: float,
        market_regime: str = "neutral",
        kelly_fraction: float = 0.25
    ) -> PositionRecommendation:
        """
        Calculate optimal position size using quantum-inspired approach.
        
        Args:
            signal_confidence: Confidence in trading signal (0-1)
            current_price: Current market price
            volatility: Market volatility (annualized)
            market_regime: Current market regime
            kelly_fraction: Fraction of Kelly criterion to use
            
        Returns:
            PositionRecommendation with size and risk parameters
        """
        # Step 1: Calculate probability amplitudes (quantum superposition)
        amplitudes = self._calculate_probability_amplitudes(
            signal_confidence, volatility, market_regime
        )
        
        # Step 2: Create quantum superposition of states
        superposition = self._create_superposition(amplitudes)
        
        # Step 3: Observe market state (wave function collapse)
        observed_state = self._observe_market_state(superposition, volatility)
        
        # Step 4: Calculate position size based on observed state
        base_position = self._calculate_base_position(
            observed_state, signal_confidence, kelly_fraction
        )
        
        # Step 5: Apply quantum constraints
        adjusted_position = self._apply_quantum_constraints(
            base_position, observed_state, volatility
        )
        
        # Step 6: Calculate stop loss and take profit
        stop_loss, take_profit = self._calculate_quantum_stops(
            current_price, observed_state, volatility, signal_confidence
        )
        
        # Step 7: Calculate uncertainty
        uncertainty = self._calculate_uncertainty(superposition, volatility)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            observed_state, adjusted_position, uncertainty, signal_confidence
        )
        
        return PositionRecommendation(
            size=adjusted_position,
            stop_loss=stop_loss,
            take_profit=take_profit,
            uncertainty=uncertainty,
            confidence=signal_confidence,
            reasoning=reasoning,
            quantum_state=superposition
        )
    
    def _calculate_probability_amplitudes(
        self,
        signal_confidence: float,
        volatility: float,
        market_regime: str
    ) -> Dict[str, float]:
        """
        Calculate probability amplitudes for different market states.
        
        In quantum mechanics, amplitude squared gives probability.
        
        Args:
            signal_confidence: Signal confidence
            volatility: Market volatility
            market_regime: Current market regime
            
        Returns:
            Dictionary of probability amplitudes
        """
        # Base amplitudes from signal
        bull_amplitude = np.sqrt(max(0, signal_confidence))
        bear_amplitude = np.sqrt(max(0, 1 - signal_confidence))
        
        # Adjust for market regime
        regime_adjustments = {
            'bull': (1.2, 0.8),
            'bear': (0.8, 1.2),
            'neutral': (1.0, 1.0),
            'ranging': (1.0, 1.0)
        }
        
        adjustment = regime_adjustments.get(market_regime.lower(), (1.0, 1.0))
        bull_amplitude *= adjustment[0]
        bear_amplitude *= adjustment[1]
        
        # Add uncertainty amplitude (minimum 10%)
        uncertainty_amplitude = np.sqrt(0.1) * (1 + volatility)
        
        # Normalize amplitudes
        total = np.sqrt(bull_amplitude**2 + bear_amplitude**2 + uncertainty_amplitude**2)
        if total > 0:
            bull_amplitude /= total
            bear_amplitude /= total
            uncertainty_amplitude /= total
        
        return {
            'bull': bull_amplitude,
            'bear': bear_amplitude,
            'neutral': uncertainty_amplitude
        }
    
    def _create_superposition(self, amplitudes: Dict[str, float]) -> Dict[str, float]:
        """
        Create quantum superposition of market states.
        
        Args:
            amplitudes: Probability amplitudes
            
        Returns:
            Dictionary of state probabilities (amplitude squared)
        """
        superposition = {}
        for state, amplitude in amplitudes.items():
            # Probability = |amplitude|^2
            superposition[state] = amplitude ** 2
        
        return superposition
    
    def _observe_market_state(
        self,
        superposition: Dict[str, float],
        volatility: float
    ) -> str:
        """
        Observe market state (wave function collapse).
        
        Higher volatility increases observation uncertainty.
        
        Args:
            superposition: Quantum superposition
            volatility: Market volatility
            
        Returns:
            Observed market state
        """
        # Add quantum noise based on volatility
        noisy_probs = {}
        for state, prob in superposition.items():
            noise = np.random.normal(0, volatility * 0.1)
            noisy_probs[state] = max(0, prob + noise)
        
        # Renormalize
        total = sum(noisy_probs.values())
        if total > 0:
            noisy_probs = {k: v/total for k, v in noisy_probs.items()}
        
        # Collapse to most probable state
        observed_state = max(noisy_probs, key=noisy_probs.get)
        
        return observed_state
    
    def _calculate_base_position(
        self,
        state: str,
        confidence: float,
        kelly_fraction: float
    ) -> float:
        """
        Calculate base position size.
        
        Args:
            state: Observed market state
            confidence: Signal confidence
            kelly_fraction: Kelly fraction to use
            
        Returns:
            Base position size (fraction of capital)
        """
        # Use modified Kelly criterion
        # f* = (p * b - q) / b
        # where p = win probability, q = 1-p, b = win/loss ratio
        
        win_prob = confidence
        win_loss_ratio = 2.0  # Assume 2:1 reward/risk target
        
        kelly_size = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
        kelly_size = max(0, kelly_size)  # No negative positions
        
        # Apply fraction for safety
        position_size = kelly_size * kelly_fraction
        
        # State-based adjustments
        state_multipliers = {
            'bull': 1.0,
            'bear': 0.8,  # More conservative in bear markets
            'neutral': 0.6  # Even more conservative in uncertain markets
        }
        
        multiplier = state_multipliers.get(state, 0.6)
        position_size *= multiplier
        
        return position_size
    
    def _apply_quantum_constraints(
        self,
        position_size: float,
        state: str,
        volatility: float
    ) -> float:
        """
        Apply quantum-inspired constraints to position size.
        
        Args:
            position_size: Raw position size
            state: Market state
            volatility: Market volatility
            
        Returns:
            Constrained position size
        """
        # Apply max risk per trade constraint
        max_position = self.max_risk_per_trade / max(volatility, 0.01)
        position_size = min(position_size, max_position)
        
        # Apply total risk constraint
        current_exposure = self._calculate_current_exposure()
        remaining_capacity = self.max_total_risk - current_exposure
        position_size = min(position_size, remaining_capacity)
        
        # Quantum uncertainty principle: reduce size in high uncertainty
        if state == 'neutral':
            position_size *= 0.5
        
        # Never exceed 100% of capital
        position_size = min(position_size, 1.0)
        
        return max(0, position_size)
    
    def _calculate_quantum_stops(
        self,
        current_price: float,
        state: str,
        volatility: float,
        confidence: float
    ) -> Tuple[float, float]:
        """
        Calculate quantum-inspired stop loss and take profit levels.
        
        Args:
            current_price: Current market price
            state: Market state
            volatility: Market volatility
            confidence: Signal confidence
            
        Returns:
            Tuple of (stop_loss, take_profit) prices
        """
        # Base stop distance on volatility (ATR-like)
        stop_distance = current_price * volatility * 2.0
        
        # Quantum adjustment: tighter stops in uncertain states
        uncertainty_factor = {'bull': 1.0, 'bear': 1.0, 'neutral': 0.7}
        stop_distance *= uncertainty_factor.get(state, 1.0)
        
        # Calculate levels based on state
        if state == 'bull':
            stop_loss = current_price - stop_distance
            take_profit = current_price + stop_distance * 3.0  # 3:1 R:R
        elif state == 'bear':
            stop_loss = current_price + stop_distance
            take_profit = current_price - stop_distance * 3.0  # Short position
        else:  # neutral
            stop_loss = current_price - stop_distance * 0.5
            take_profit = current_price + stop_distance * 1.5  # 1.5:1 R:R
        
        return stop_loss, take_profit
    
    def _calculate_uncertainty(
        self,
        superposition: Dict[str, float],
        volatility: float
    ) -> float:
        """
        Calculate quantum uncertainty.
        
        Higher entropy in superposition = higher uncertainty.
        
        Args:
            superposition: Quantum state superposition
            volatility: Market volatility
            
        Returns:
            Uncertainty score (0-1)
        """
        # Shannon entropy as measure of uncertainty
        entropy = 0.0
        for prob in superposition.values():
            if prob > 0:
                entropy -= prob * np.log2(prob)
        
        # Normalize to 0-1 range (max entropy for 3 states = log2(3))
        max_entropy = np.log2(len(superposition))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        # Combine with volatility
        uncertainty = (normalized_entropy + volatility) / 2
        
        return min(1.0, uncertainty)
    
    def _calculate_current_exposure(self) -> float:
        """Calculate current portfolio exposure."""
        # Placeholder - in production, would check actual positions
        return 0.0
    
    def _generate_reasoning(
        self,
        state: str,
        position_size: float,
        uncertainty: float,
        confidence: float
    ) -> str:
        """Generate human-readable reasoning."""
        reasoning = f"Quantum Risk Analysis:\n"
        reasoning += f"- Observed State: {state.upper()}\n"
        reasoning += f"- Position Size: {position_size:.2%} of capital\n"
        reasoning += f"- Quantum Uncertainty: {uncertainty:.2%}\n"
        reasoning += f"- Signal Confidence: {confidence:.2%}\n"
        reasoning += f"- Risk per Trade: {self.max_risk_per_trade:.2%}\n"
        
        if uncertainty > 0.7:
            reasoning += "⚠️ High uncertainty - reduced position size\n"
        elif uncertainty < 0.3:
            reasoning += "✓ Low uncertainty - full position allowed\n"
        
        return reasoning


class AdaptivePositionSizer:
    """
    Adaptive position sizing based on recent performance.
    """
    
    def __init__(self, lookback_window: int = 20):
        """
        Initialize adaptive position sizer.
        
        Args:
            lookback_window: Number of recent trades to consider
        """
        self.lookback_window = lookback_window
        self.trade_history = []
    
    def adjust_size(
        self,
        base_size: float,
        recent_performance: List[float]
    ) -> float:
        """
        Adjust position size based on recent performance.
        
        Args:
            base_size: Base position size
            recent_performance: List of recent trade returns
            
        Returns:
            Adjusted position size
        """
        if len(recent_performance) < 5:
            return base_size
        
        # Calculate win rate
        wins = sum(1 for ret in recent_performance if ret > 0)
        win_rate = wins / len(recent_performance)
        
        # Adjust size based on performance
        if win_rate > 0.6:
            return base_size * 1.2  # Increase size
        elif win_rate < 0.4:
            return base_size * 0.8  # Decrease size
        else:
            return base_size


class QuantumCircuitBreaker:
    """
    Quantum-inspired circuit breaker for risk management.
    """
    
    def __init__(
        self,
        daily_loss_limit: float = 0.05,
        max_drawdown: float = 0.10
    ):
        """
        Initialize circuit breaker.
        
        Args:
            daily_loss_limit: Maximum daily loss (fraction)
            max_drawdown: Maximum drawdown (fraction)
        """
        self.daily_loss_limit = daily_loss_limit
        self.max_drawdown = max_drawdown
        self.daily_pnl = 0.0
        self.peak_capital = 0.0
        self.current_capital = 0.0
    
    def should_halt_trading(self) -> Tuple[bool, str]:
        """
        Check if trading should be halted.
        
        Returns:
            Tuple of (should_halt, reason)
        """
        # Check daily loss limit
        if self.daily_pnl < -self.daily_loss_limit:
            return True, f"Daily loss limit exceeded: {self.daily_pnl:.2%}"
        
        # Check drawdown
        if self.current_capital > 0 and self.peak_capital > 0:
            drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
            if drawdown > self.max_drawdown:
                return True, f"Max drawdown exceeded: {drawdown:.2%}"
        
        return False, ""
