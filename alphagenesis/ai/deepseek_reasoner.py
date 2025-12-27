"""
DeepSeek Reasoner - AI Reasoning Layer for AlphaGenesis

This module implements the "long chain-of-thought" reasoning that was the key
differentiator in Alpha Arena, where DeepSeek achieved 130%+ returns.

Key Insight: "Longer reasoning chains correlated with stricter decision-making"
- DeepSeek had the LONGEST reasoning chains
- This led to FEWER but HIGHER QUALITY trades
- Result: 35% in 3 days, 130% in 10 days

This module acts as the FINAL GATEKEEPER for all trade signals.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from loguru import logger


class MarketRegime(Enum):
    """Market regime classification."""
    STRONG_UPTREND = "strong_uptrend"
    WEAK_UPTREND = "weak_uptrend"
    RANGING = "ranging"
    WEAK_DOWNTREND = "weak_downtrend"
    STRONG_DOWNTREND = "strong_downtrend"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


class TradeAction(Enum):
    """Possible trade actions."""
    HOLD = "HOLD"
    LONG = "LONG"
    SHORT = "SHORT"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""
    step_number: int
    check_name: str
    passed: bool
    value: Any
    threshold: Any
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TradeDecision:
    """
    Final trade decision with full reasoning chain.
    
    This mirrors DeepSeek's output format from Alpha Arena:
    SIDE | COIN | LEVERAGE | NOTIONAL | EXIT PLAN | REASONING
    """
    action: TradeAction
    symbol: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    leverage: float
    position_size: float
    risk_reward_ratio: float
    confidence: float
    reasoning_chain: List[ReasoningStep]
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_trade(self) -> bool:
        """Check if this decision results in a trade."""
        return self.action not in [TradeAction.HOLD]
    
    @property
    def reasoning_summary(self) -> str:
        """Get human-readable reasoning summary."""
        lines = [f"Decision: {self.action.value} {self.symbol}"]
        lines.append(f"Reasoning Chain ({len(self.reasoning_chain)} steps):")
        for step in self.reasoning_chain:
            status = "✓" if step.passed else "✗"
            lines.append(f"  {status} Step {step.step_number}: {step.check_name}")
            lines.append(f"      {step.reasoning}")
        return "\n".join(lines)


class DeepSeekReasoner:
    """
    AI Reasoning Layer implementing DeepSeek's winning strategy.
    
    This is the FINAL GATEKEEPER for all trade signals. Every potential trade
    must pass through a multi-step reasoning chain before execution.
    
    Key principles from Alpha Arena:
    1. Low frequency - only trade when ALL conditions align
    2. Long holds - minimum hold time enforced
    3. High R:R - minimum 3:1 risk-reward required
    4. Strict discipline - no emotional/impulsive trades
    
    The longer the reasoning chain, the stricter the decision-making.
    """
    
    # Configuration constants (from Alpha Arena winning strategy)
    MIN_CONFLUENCE_SCORE = 0.7  # 70% of timeframes must agree
    MIN_RISK_REWARD = 3.0       # Minimum 3:1 R:R ratio
    MAX_LEVERAGE = 15.0         # Conservative cap (under WEEX's 20x)
    MIN_HOLD_HOURS = 4          # Minimum position duration
    MAX_DAILY_TRADES = 3        # Prevent overtrading
    MIN_SIGNAL_CONFIDENCE = 0.6 # Minimum model confidence
    
    # Regime-specific parameters
    TRADEABLE_REGIMES = [
        MarketRegime.STRONG_UPTREND,
        MarketRegime.STRONG_DOWNTREND,
    ]

    def __init__(
        self,
        min_confluence: float = 0.7,
        min_risk_reward: float = 3.0,
        max_leverage: float = 15.0,
        min_hold_hours: int = 4,
        max_daily_trades: int = 3,
    ):
        """
        Initialize the DeepSeek Reasoner.
        
        Args:
            min_confluence: Minimum multi-timeframe confluence score (0-1)
            min_risk_reward: Minimum risk-reward ratio for trades
            max_leverage: Maximum allowed leverage
            min_hold_hours: Minimum hours to hold a position
            max_daily_trades: Maximum trades per day
        """
        self.min_confluence = min_confluence
        self.min_risk_reward = min_risk_reward
        self.max_leverage = max_leverage
        self.min_hold_hours = min_hold_hours
        self.max_daily_trades = max_daily_trades
        
        # State tracking
        self.trades_today = 0
        self.last_trade_date = None
        self.open_positions: Dict[str, datetime] = {}
        self.decision_history: List[TradeDecision] = []
        
        logger.info(
            f"DeepSeek Reasoner initialized: "
            f"min_confluence={min_confluence}, min_rr={min_risk_reward}, "
            f"max_leverage={max_leverage}"
        )
    
    def evaluate_trade_signal(
        self,
        symbol: str,
        proposed_signal: Dict[str, Any],
        market_context: Dict[str, Any],
    ) -> TradeDecision:
        """
        Evaluate a proposed trade signal through the full reasoning chain.
        
        This is the core method implementing DeepSeek's disciplined approach.
        A trade is ONLY executed if ALL checks pass.
        
        Args:
            symbol: Trading pair (e.g., 'cmt_btcusdt')
            proposed_signal: Signal from ML models containing:
                - direction: 'LONG' or 'SHORT'
                - confidence: 0-1 model confidence
                - suggested_leverage: Model's leverage suggestion
            market_context: Current market data containing:
                - current_price: Latest price
                - atr: Average True Range
                - prices_1h, prices_4h, prices_1d: Price series
                - volume: Current volume
                - funding_rate: Perpetual funding rate
                
        Returns:
            TradeDecision with action and full reasoning chain
        """
        reasoning_chain: List[ReasoningStep] = []
        step_num = 0
        
        # Default to HOLD
        decision = self._create_hold_decision(symbol, reasoning_chain)
        
        logger.info(f"Evaluating signal for {symbol}: {proposed_signal}")

        # =====================================================================
        # STEP 1: Daily Trade Limit Check
        # =====================================================================
        step_num += 1
        self._reset_daily_counter()
        
        if self.trades_today >= self.max_daily_trades:
            reasoning_chain.append(ReasoningStep(
                step_number=step_num,
                check_name="Daily Trade Limit",
                passed=False,
                value=self.trades_today,
                threshold=self.max_daily_trades,
                reasoning=f"Already executed {self.trades_today} trades today. "
                          f"Max is {self.max_daily_trades}. HOLD to prevent overtrading."
            ))
            return self._create_hold_decision(symbol, reasoning_chain)
        
        reasoning_chain.append(ReasoningStep(
            step_number=step_num,
            check_name="Daily Trade Limit",
            passed=True,
            value=self.trades_today,
            threshold=self.max_daily_trades,
            reasoning=f"Trade count ({self.trades_today}) within daily limit ({self.max_daily_trades})."
        ))
        
        # =====================================================================
        # STEP 2: Signal Confidence Check
        # =====================================================================
        step_num += 1
        signal_confidence = proposed_signal.get('confidence', 0.0)
        
        if signal_confidence < self.MIN_SIGNAL_CONFIDENCE:
            reasoning_chain.append(ReasoningStep(
                step_number=step_num,
                check_name="Signal Confidence",
                passed=False,
                value=signal_confidence,
                threshold=self.MIN_SIGNAL_CONFIDENCE,
                reasoning=f"Model confidence ({signal_confidence:.2f}) below threshold "
                          f"({self.MIN_SIGNAL_CONFIDENCE}). Signal too weak. HOLD."
            ))
            return self._create_hold_decision(symbol, reasoning_chain)
        
        reasoning_chain.append(ReasoningStep(
            step_number=step_num,
            check_name="Signal Confidence",
            passed=True,
            value=signal_confidence,
            threshold=self.MIN_SIGNAL_CONFIDENCE,
            reasoning=f"Model confidence ({signal_confidence:.2f}) meets threshold."
        ))

        # =====================================================================
        # STEP 3: Market Regime Assessment
        # =====================================================================
        step_num += 1
        regime = self._assess_market_regime(market_context)
        
        if regime not in self.TRADEABLE_REGIMES:
            reasoning_chain.append(ReasoningStep(
                step_number=step_num,
                check_name="Market Regime",
                passed=False,
                value=regime.value,
                threshold=[r.value for r in self.TRADEABLE_REGIMES],
                reasoning=f"Market regime is '{regime.value}'. "
                          f"Only trade in strong trends. HOLD."
            ))
            return self._create_hold_decision(symbol, reasoning_chain)
        
        reasoning_chain.append(ReasoningStep(
            step_number=step_num,
            check_name="Market Regime",
            passed=True,
            value=regime.value,
            threshold=[r.value for r in self.TRADEABLE_REGIMES],
            reasoning=f"Market in '{regime.value}' - favorable for trading."
        ))
        
        # =====================================================================
        # STEP 4: Multi-Timeframe Confluence
        # =====================================================================
        step_num += 1
        confluence_score = self._calculate_confluence_score(
            market_context,
            timeframes=['1h', '4h', '1d']
        )
        
        if confluence_score < self.min_confluence:
            reasoning_chain.append(ReasoningStep(
                step_number=step_num,
                check_name="Multi-Timeframe Confluence",
                passed=False,
                value=confluence_score,
                threshold=self.min_confluence,
                reasoning=f"Confluence score ({confluence_score:.2f}) below threshold "
                          f"({self.min_confluence}). Timeframes not aligned. HOLD."
            ))
            return self._create_hold_decision(symbol, reasoning_chain)
        
        reasoning_chain.append(ReasoningStep(
            step_number=step_num,
            check_name="Multi-Timeframe Confluence",
            passed=True,
            value=confluence_score,
            threshold=self.min_confluence,
            reasoning=f"Confluence score ({confluence_score:.2f}) shows strong alignment."
        ))

        # =====================================================================
        # STEP 5: Risk-Reward Calculation
        # =====================================================================
        step_num += 1
        current_price = market_context.get('current_price', 0)
        atr = market_context.get('atr', 0)
        direction = proposed_signal.get('direction', 'LONG')
        
        entry_price, stop_loss, take_profit, risk_reward = self._calculate_risk_reward(
            current_price=current_price,
            atr=atr,
            direction=direction
        )
        
        if risk_reward < self.min_risk_reward:
            reasoning_chain.append(ReasoningStep(
                step_number=step_num,
                check_name="Risk-Reward Ratio",
                passed=False,
                value=risk_reward,
                threshold=self.min_risk_reward,
                reasoning=f"Risk-Reward ({risk_reward:.1f}:1) below minimum "
                          f"({self.min_risk_reward}:1). Trade not worth the risk. HOLD."
            ))
            return self._create_hold_decision(symbol, reasoning_chain)
        
        reasoning_chain.append(ReasoningStep(
            step_number=step_num,
            check_name="Risk-Reward Ratio",
            passed=True,
            value=risk_reward,
            threshold=self.min_risk_reward,
            reasoning=f"Risk-Reward ({risk_reward:.1f}:1) exceeds minimum. Favorable setup."
        ))
        
        # =====================================================================
        # STEP 6: Funding Rate Check (Perpetuals Edge)
        # =====================================================================
        step_num += 1
        funding_rate = market_context.get('funding_rate', 0)
        funding_aligned = self._check_funding_alignment(funding_rate, direction)
        
        if not funding_aligned:
            reasoning_chain.append(ReasoningStep(
                step_number=step_num,
                check_name="Funding Rate Alignment",
                passed=False,
                value=funding_rate,
                threshold="Aligned with direction",
                reasoning=f"Funding rate ({funding_rate:.4f}) not aligned with {direction}. "
                          f"Trading against funding. Proceed with caution."
            ))
            # This is a soft check - we don't reject but note it
        else:
            reasoning_chain.append(ReasoningStep(
                step_number=step_num,
                check_name="Funding Rate Alignment",
                passed=True,
                value=funding_rate,
                threshold="Aligned with direction",
                reasoning=f"Funding rate ({funding_rate:.4f}) supports {direction} position."
            ))

        # =====================================================================
        # STEP 7: Position Sizing (Kelly Criterion)
        # =====================================================================
        step_num += 1
        account_balance = market_context.get('account_balance', 1000)
        
        position_size, leverage = self._calculate_position_size(
            confidence=signal_confidence,
            account_balance=account_balance,
            risk_reward=risk_reward,
            atr=atr,
            current_price=current_price
        )
        
        reasoning_chain.append(ReasoningStep(
            step_number=step_num,
            check_name="Position Sizing",
            passed=True,
            value=f"Size: {position_size:.4f}, Leverage: {leverage:.1f}x",
            threshold=f"Max Leverage: {self.max_leverage}x",
            reasoning=f"Kelly-based sizing: {position_size:.4f} units at {leverage:.1f}x leverage."
        ))
        
        # =====================================================================
        # STEP 8: Final Validation
        # =====================================================================
        step_num += 1
        
        # All checks passed - generate trade decision
        action = TradeAction.LONG if direction == 'LONG' else TradeAction.SHORT
        
        reasoning_chain.append(ReasoningStep(
            step_number=step_num,
            check_name="Final Validation",
            passed=True,
            value="ALL CHECKS PASSED",
            threshold="8/8 checks",
            reasoning=f"All {step_num} reasoning steps passed. EXECUTE {action.value}."
        ))
        
        # Create the final trade decision
        decision = TradeDecision(
            action=action,
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            leverage=leverage,
            position_size=position_size,
            risk_reward_ratio=risk_reward,
            confidence=signal_confidence,
            reasoning_chain=reasoning_chain
        )
        
        # Update state
        self.trades_today += 1
        self.open_positions[symbol] = datetime.now()
        self.decision_history.append(decision)
        
        logger.info(f"TRADE APPROVED: {decision.reasoning_summary}")
        
        return decision

    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _create_hold_decision(
        self, 
        symbol: str, 
        reasoning_chain: List[ReasoningStep]
    ) -> TradeDecision:
        """Create a HOLD decision with reasoning."""
        return TradeDecision(
            action=TradeAction.HOLD,
            symbol=symbol,
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            leverage=0.0,
            position_size=0.0,
            risk_reward_ratio=0.0,
            confidence=0.0,
            reasoning_chain=reasoning_chain
        )
    
    def _reset_daily_counter(self):
        """Reset daily trade counter if it's a new day."""
        today = datetime.now().date()
        if self.last_trade_date != today:
            self.trades_today = 0
            self.last_trade_date = today
    
    def _assess_market_regime(self, market_context: Dict) -> MarketRegime:
        """
        Assess current market regime using price action and volatility.
        
        Uses:
        - EMA slopes for trend direction
        - ATR percentile for volatility assessment
        - Price position relative to moving averages
        """
        prices = market_context.get('prices_1h', [])
        if len(prices) < 50:
            return MarketRegime.RANGING
        
        prices = np.array(prices)
        
        # Calculate EMAs
        ema_20 = self._ema(prices, 20)
        ema_50 = self._ema(prices, 50)
        
        # EMA slopes (trend strength)
        ema_20_slope = (ema_20[-1] - ema_20[-5]) / ema_20[-5] if ema_20[-5] != 0 else 0
        ema_50_slope = (ema_50[-1] - ema_50[-5]) / ema_50[-5] if ema_50[-5] != 0 else 0
        
        # Current price position
        current_price = prices[-1]
        price_above_ema20 = current_price > ema_20[-1]
        price_above_ema50 = current_price > ema_50[-1]
        ema20_above_ema50 = ema_20[-1] > ema_50[-1]
        
        # Volatility assessment
        atr = market_context.get('atr', 0)
        avg_price = np.mean(prices[-20:])
        volatility_pct = (atr / avg_price) * 100 if avg_price > 0 else 0
        
        # Regime classification
        if volatility_pct > 5:  # Very high volatility
            return MarketRegime.HIGH_VOLATILITY
        
        if ema_20_slope > 0.02 and ema_50_slope > 0.01 and price_above_ema20 and ema20_above_ema50:
            return MarketRegime.STRONG_UPTREND
        elif ema_20_slope > 0.01 and price_above_ema50:
            return MarketRegime.WEAK_UPTREND
        elif ema_20_slope < -0.02 and ema_50_slope < -0.01 and not price_above_ema20 and not ema20_above_ema50:
            return MarketRegime.STRONG_DOWNTREND
        elif ema_20_slope < -0.01 and not price_above_ema50:
            return MarketRegime.WEAK_DOWNTREND
        else:
            return MarketRegime.RANGING

    def _calculate_confluence_score(
        self, 
        market_context: Dict,
        timeframes: List[str]
    ) -> float:
        """
        Calculate multi-timeframe confluence score.
        
        Score is 0-1 representing how many timeframes agree on direction.
        1.0 = all timeframes bullish or all bearish
        0.5 = mixed signals
        0.0 = no data
        """
        bullish_count = 0
        bearish_count = 0
        total_timeframes = 0
        
        for tf in timeframes:
            prices_key = f'prices_{tf}'
            prices = market_context.get(prices_key, [])
            
            if len(prices) < 20:
                continue
            
            total_timeframes += 1
            prices = np.array(prices)
            
            # Simple trend determination: EMA crossover
            ema_fast = self._ema(prices, 8)
            ema_slow = self._ema(prices, 21)
            
            if ema_fast[-1] > ema_slow[-1]:
                bullish_count += 1
            else:
                bearish_count += 1
        
        if total_timeframes == 0:
            return 0.0
        
        # Confluence is how aligned the timeframes are
        max_agreement = max(bullish_count, bearish_count)
        confluence = max_agreement / total_timeframes
        
        return confluence
    
    def _calculate_risk_reward(
        self,
        current_price: float,
        atr: float,
        direction: str
    ) -> Tuple[float, float, float, float]:
        """
        Calculate entry, stop-loss, take-profit, and R:R ratio.
        
        Uses ATR-based stops for volatility-adjusted risk management.
        """
        if atr <= 0:
            atr = current_price * 0.01  # Default to 1% if no ATR
        
        # Stop-loss at 2 ATR
        # Take-profit at 6 ATR (3:1 R:R)
        stop_distance = 2 * atr
        profit_distance = 6 * atr  # 3:1 R:R
        
        if direction == 'LONG':
            entry_price = current_price
            stop_loss = current_price - stop_distance
            take_profit = current_price + profit_distance
        else:  # SHORT
            entry_price = current_price
            stop_loss = current_price + stop_distance
            take_profit = current_price - profit_distance
        
        # Calculate actual R:R
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward = reward / risk if risk > 0 else 0
        
        return entry_price, stop_loss, take_profit, risk_reward

    def _check_funding_alignment(self, funding_rate: float, direction: str) -> bool:
        """
        Check if funding rate supports the trade direction.
        
        High positive funding = shorts get paid = good for shorts
        High negative funding = longs get paid = good for longs
        """
        if direction == 'LONG':
            # Prefer going long when funding is negative (longs get paid)
            return funding_rate <= 0.001  # Allow small positive funding
        else:  # SHORT
            # Prefer going short when funding is positive (shorts get paid)
            return funding_rate >= -0.001
    
    def _calculate_position_size(
        self,
        confidence: float,
        account_balance: float,
        risk_reward: float,
        atr: float,
        current_price: float
    ) -> Tuple[float, float]:
        """
        Calculate optimal position size using Kelly Criterion variant.
        
        Kelly = (Win% * AvgWin - Loss% * AvgLoss) / AvgWin
        
        We use a conservative 1/4 Kelly.
        """
        # Estimate win rate based on confidence and R:R
        estimated_win_rate = confidence * 0.8  # Conservative estimate
        
        # Kelly calculation
        avg_win = risk_reward  # Normalized
        avg_loss = 1.0  # Normalized
        loss_rate = 1 - estimated_win_rate
        
        kelly = (estimated_win_rate * avg_win - loss_rate * avg_loss) / avg_win
        kelly = max(0, min(kelly, 0.25))  # Cap at 25%
        
        # Use 1/4 Kelly for safety
        position_fraction = kelly * 0.25
        
        # Never risk more than 2% per trade
        max_risk_fraction = 0.02
        position_fraction = min(position_fraction, max_risk_fraction)
        
        # Calculate actual position size
        risk_per_trade = account_balance * position_fraction
        stop_distance = 2 * atr
        
        if stop_distance > 0 and current_price > 0:
            # Position size in base currency (BTC)
            position_value = risk_per_trade / (stop_distance / current_price)
            position_size = position_value / current_price
        else:
            position_size = 0.001  # Minimum
        
        # Calculate required leverage
        notional_value = position_size * current_price
        leverage = notional_value / account_balance if account_balance > 0 else 1
        leverage = min(leverage, self.max_leverage)  # Cap leverage
        
        return position_size, leverage
    
    def _ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        alpha = 2 / (period + 1)
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        
        return ema

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def can_close_position(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if a position can be closed (minimum hold time).
        """
        if symbol not in self.open_positions:
            return True, "No open position"
        
        open_time = self.open_positions[symbol]
        hold_duration = datetime.now() - open_time
        min_hold = timedelta(hours=self.min_hold_hours)
        
        if hold_duration < min_hold:
            remaining = min_hold - hold_duration
            return False, f"Minimum hold time not met. {remaining} remaining."
        
        return True, "Position can be closed"
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """Get statistics on reasoning decisions."""
        total = len(self.decision_history)
        trades = sum(1 for d in self.decision_history if d.is_trade)
        holds = total - trades
        
        avg_steps = np.mean([len(d.reasoning_chain) for d in self.decision_history]) if total > 0 else 0
        
        return {
            'total_evaluations': total,
            'trades_executed': trades,
            'holds': holds,
            'trade_rate': trades / total if total > 0 else 0,
            'avg_reasoning_steps': avg_steps,
            'trades_today': self.trades_today,
        }
    
    def export_reasoning_log(self, filepath: str):
        """Export full reasoning history for analysis."""
        import json
        
        log = []
        for decision in self.decision_history:
            entry = {
                'timestamp': decision.timestamp.isoformat(),
                'symbol': decision.symbol,
                'action': decision.action.value,
                'confidence': decision.confidence,
                'risk_reward': decision.risk_reward_ratio,
                'reasoning_steps': len(decision.reasoning_chain),
                'reasoning': [
                    {
                        'step': s.step_number,
                        'check': s.check_name,
                        'passed': s.passed,
                        'reasoning': s.reasoning
                    }
                    for s in decision.reasoning_chain
                ]
            }
            log.append(entry)
        
        with open(filepath, 'w') as f:
            json.dump(log, f, indent=2)
        
        logger.info(f"Exported {len(log)} decisions to {filepath}")


# Module initialization
__all__ = [
    'DeepSeekReasoner',
    'TradeDecision',
    'TradeAction',
    'MarketRegime',
    'ReasoningStep'
]
