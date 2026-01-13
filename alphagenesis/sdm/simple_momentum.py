"""
Simple Momentum Strategy for Competition
Uses proven technical indicators instead of untrained ML models.
"""
import numpy as np
from typing import Dict, Optional, Tuple
from loguru import logger


class SimpleMomentumStrategy:
    """
    Simple but effective momentum strategy using:
    - RSI for overbought/oversold
    - Moving average crossovers for trend
    - Volume confirmation
    - Clear risk management
    """

    def __init__(self):
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
        symbol: str
    ) -> Optional[Dict]:
        """
        Generate trading signal based on momentum.

        Returns:
            Dict with direction and confidence, or None if no signal
        """
        try:
            # Extract close prices from candles
            closes = []
            for c in candles:
                if isinstance(c, dict):
                    closes.append(float(c.get('close', 0)))
                elif isinstance(c, list) and len(c) >= 5:
                    closes.append(float(c[4]))

            if len(closes) < 50:
                return None

            prices = np.array(closes)

            # Calculate indicators
            rsi = self.calculate_rsi(prices)
            ma_fast = self.calculate_ma(prices, self.ma_fast)
            ma_slow = self.calculate_ma(prices, self.ma_slow)

            # Calculate momentum
            momentum = (prices[-1] - prices[-10]) / prices[-10] * 100

            # Price position relative to moving averages
            price_above_ma = current_price > ma_fast and current_price > ma_slow
            price_below_ma = current_price < ma_fast and current_price < ma_slow

            # MA crossover
            ma_bullish = ma_fast > ma_slow
            ma_bearish = ma_fast < ma_slow

            logger.info(f"{symbol} - RSI: {rsi:.1f}, MA Fast: {ma_fast:.2f}, MA Slow: {ma_slow:.2f}, Momentum: {momentum:.2f}%")

            # REVERSAL SIGNALS - Extreme RSI overrides everything
            # When RSI is VERY oversold/overbought, market often reverses
            if rsi < 25:  # Extremely oversold - buy the dip!
                confidence = min(0.85, (25 - rsi) / 15)
                logger.info(f"🟢 REVERSAL LONG signal for {symbol}: RSI extremely oversold at {rsi:.1f}")
                return {
                    'direction': 'LONG',
                    'confidence': confidence,
                    'reason': f'RSI={rsi:.1f} extremely oversold - reversal play'
                }

            if rsi > 75:  # Extremely overbought - short the top!
                confidence = min(0.85, (rsi - 75) / 15)
                logger.info(f"🔴 REVERSAL SHORT signal for {symbol}: RSI extremely overbought at {rsi:.1f}")
                return {
                    'direction': 'SHORT',
                    'confidence': confidence,
                    'reason': f'RSI={rsi:.1f} extremely overbought - reversal play'
                }

            # LONG signals (original logic)
            if (rsi < self.rsi_oversold and
                ma_bullish and
                momentum < -3 and
                price_below_ma):
                confidence = min(0.8, (self.rsi_oversold - rsi) / 20)
                logger.info(f"🟢 LONG signal for {symbol}: RSI oversold + bullish MA + negative momentum")
                return {
                    'direction': 'LONG',
                    'confidence': confidence,
                    'reason': f'RSI={rsi:.1f} oversold, bullish MA cross, momentum={momentum:.1f}%'
                }

            # SHORT signals (original logic)
            if (rsi > self.rsi_overbought and
                ma_bearish and
                momentum > 3 and
                price_above_ma):
                confidence = min(0.8, (rsi - self.rsi_overbought) / 20)
                logger.info(f"🔴 SHORT signal for {symbol}: RSI overbought + bearish MA + positive momentum")
                return {
                    'direction': 'SHORT',
                    'confidence': confidence,
                    'reason': f'RSI={rsi:.1f} overbought, bearish MA cross, momentum={momentum:.1f}%'
                }

            # Strong momentum plays (regardless of RSI)
            if abs(momentum) > 10:
                if momentum > 10 and ma_bullish and rsi < 80:
                    logger.info(f"🚀 Strong LONG momentum for {symbol}: {momentum:.1f}%")
                    return {
                        'direction': 'LONG',
                        'confidence': 0.7,
                        'reason': f'Strong upward momentum {momentum:.1f}%'
                    }
                elif momentum < -10 and ma_bearish and rsi > 20:
                    logger.info(f"📉 Strong SHORT momentum for {symbol}: {momentum:.1f}%")
                    return {
                        'direction': 'SHORT',
                        'confidence': 0.7,
                        'reason': f'Strong downward momentum {momentum:.1f}%'
                    }

            return None

        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None

    def should_close_position(
        self,
        entry_price: float,
        current_price: float,
        direction: str,
        time_held_minutes: int
    ) -> Tuple[bool, str]:
        """
        Determine if we should close a position.

        Returns:
            (should_close, reason)
        """
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if direction == 'LONG' else ((entry_price - current_price) / entry_price * 100)

        # Take profit at 5%
        if pnl_pct > 5:
            return True, f"Take profit at {pnl_pct:.1f}%"

        # Stop loss at -2%
        if pnl_pct < -2:
            return True, f"Stop loss at {pnl_pct:.1f}%"

        # Time-based exit if not profitable after 30 minutes
        if time_held_minutes > 30 and pnl_pct < 0.5:
            return True, f"Time exit after {time_held_minutes}min with {pnl_pct:.1f}% P&L"

        return False, ""
