"""
Momentum Trend-Following Strategy for Competition
PIVOTED: From counter-trend reversals to trend-following momentum
Strategy: Ride the trend with tight stops for competition wins
"""
import numpy as np
from typing import Dict, Optional, Tuple
from loguru import logger
from alphagenesis.features.momentum_hybrid_engine import MomentumHybridEngine


class SimpleMomentumStrategy:
    """
    Simple but effective momentum strategy using:
    - RSI for overbought/oversold
    - Moving average crossovers for trend
    - Volume confirmation
    - Clear risk management
    """

    def __init__(self):
        # PIVOTED: Use momentum hybrid engine for trend-following
        self.momentum_engine = MomentumHybridEngine()
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.ma_fast = 9
        self.ma_slow = 21

    def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_ma(self, prices: np.ndarray, period: int) -> float:
        """Calculate simple moving average."""
        if len(prices) < period:
            return prices[-1]
        return np.mean(prices[-period:])

    def generate_signal(
        self,
        candles: list,
        current_price: float,
        symbol: str,
        regime=None,
        **kwargs
    ) -> Optional[Dict]:
        """
        Generate trading signal - PIVOTED TO MOMENTUM TREND-FOLLOWING.

        NEW STRATEGY:
        - Ride uptrends (RSI > 55, EMA20 > EMA50)
        - Ride downtrends (RSI < 45, EMA20 < EMA50)
        - Tight stops (0.5-1%), quick profits (1.5-2.5%)
        - Only rare extreme reversals (RSI < 20 or > 80)

        Returns:
            Dict with direction and confidence, or None if no signal
        """
        try:
            # Use the momentum hybrid engine for signal generation
            signal = self.momentum_engine.generate_signal(
                candles=candles,
                current_price=current_price,
                symbol=symbol,
                regime=regime,
                model_confidence=0.6  # Can be replaced with actual ML model output
            )

            return signal

        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None

    def should_close_position(
        self,
        entry_price: float,
        current_price: float,
        direction: str,
        time_held_minutes: int,
        stop_loss_pct: float = 0.008,  # Competition: tighter 0.8% stop
        take_profit_pct: float = 0.02   # Competition: quick 2% profit
    ) -> Tuple[bool, str]:
        """
        COMPETITION-OPTIMIZED EXIT LOGIC.
        Tight stops, quick profits, many small wins.

        Returns:
            (should_close, reason)
        """
        pnl_pct = ((current_price - entry_price) / entry_price) if direction == 'LONG' else ((entry_price - current_price) / entry_price)

        # Quick take profit (1.5-2.5%)
        if pnl_pct > take_profit_pct:
            return True, f"✅ Take profit at {pnl_pct*100:.2f}%"

        # Tight stop loss (0.5-1%)
        if pnl_pct < -stop_loss_pct:
            return True, f"❌ Stop loss at {pnl_pct*100:.2f}%"

        # Trailing stop: If we're up 1%, trail by 0.5%
        if pnl_pct > 0.01:
            if pnl_pct < 0.005:  # Dropped from +1% to +0.5%
                return True, f"📉 Trailing stop at {pnl_pct*100:.2f}%"

        # Time-based exit: Close break-even or small loss after 45min
        if time_held_minutes > 45 and pnl_pct < 0.005:
            return True, f"⏰ Time exit after {time_held_minutes}min with {pnl_pct*100:.2f}% P&L"

        # Emergency time exit: Force close after 90min regardless
        if time_held_minutes > 90:
            return True, f"⏱️ Max hold time exit: {time_held_minutes}min, P&L: {pnl_pct*100:.2f}%"

        return False, ""
