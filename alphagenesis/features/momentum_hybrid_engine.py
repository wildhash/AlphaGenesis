"""
Momentum Hybrid Engine - Competition Edition
Trend-following strategy with AI confirmation for WEEX AI Wars
"""
import numpy as np
from typing import Dict, Optional
from loguru import logger


class MomentumHybridEngine:
    """
    Generates signals by fusing:
    1. Trend-following technical indicators (primary)
    2. Volatility-adjusted position sizing
    3. Competition-optimized risk parameters
    """

    def __init__(self):
        self.ema_fast = 20
        self.ema_slow = 50
        self.rsi_period = 14

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
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

    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate exponential moving average."""
        if len(prices) < period:
            return prices[-1]

        multiplier = 2 / (period + 1)
        ema = prices[-period]  # Start with SMA

        for price in prices[-period+1:]:
            ema = (price - ema) * multiplier + ema

        return ema

    def _calculate_atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(closes) < period + 1:
            return abs(highs[-1] - lows[-1])

        tr_list = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            tr_list.append(tr)

        return np.mean(tr_list[-period:])

    def generate_signal(
        self,
        candles: list,
        current_price: float,
        symbol: str,
        model_confidence: float = 0.6
    ) -> Optional[Dict]:
        """
        Generate MOMENTUM/TREND-FOLLOWING signal (NOT reversal).

        Strategy:
        - LONG: Uptrend confirmed (EMA20 > EMA50, RSI > 55, price > EMA20)
        - SHORT: Downtrend confirmed (EMA20 < EMA50, RSI < 45, price < EMA20)

        Returns signal dict or None
        """
        try:
            # Extract OHLC data
            closes = []
            highs = []
            lows = []

            for c in candles:
                if isinstance(c, dict):
                    closes.append(float(c.get('close', 0)))
                    highs.append(float(c.get('high', 0)))
                    lows.append(float(c.get('low', 0)))
                elif isinstance(c, list) and len(c) >= 5:
                    closes.append(float(c[4]))  # Close
                    highs.append(float(c[2]))   # High
                    lows.append(float(c[3]))    # Low

            if len(closes) < 50:
                return None

            prices = np.array(closes)
            highs_arr = np.array(highs)
            lows_arr = np.array(lows)

            # Calculate indicators
            ema_fast = self._calculate_ema(prices, self.ema_fast)
            ema_slow = self._calculate_ema(prices, self.ema_slow)
            rsi = self._calculate_rsi(prices)
            atr = self._calculate_atr(highs_arr, lows_arr, prices)

            # Trend detection
            trend_up = ema_fast > ema_slow
            trend_down = ema_fast < ema_slow

            # Momentum (10-period rate of change)
            momentum_pct = ((prices[-1] - prices[-10]) / prices[-10]) * 100

            logger.info(f"{symbol} - RSI: {rsi:.1f}, EMA20: {ema_fast:.2f}, EMA50: {ema_slow:.2f}, Momentum: {momentum_pct:.2f}%")

            # === UPTREND MOMENTUM LONG ===
            # LOOSENED: Enter when trend is UP - removed strict RSI and price filters
            # More aggressive for competition: catch the trend early
            if (trend_up and
                rsi > 45 and rsi < 78 and  # LOOSENED: from 55 to 45
                momentum_pct > 0.3):  # LOOSENED: from 1.0% to 0.3%

                # Confidence scales with signal strength
                base_confidence = min(0.45 + (rsi - 45) / 60, 0.80)  # Higher base confidence
                total_confidence = (base_confidence * 0.7) + (model_confidence * 0.3)

                # WIDENED stops for crypto volatility
                stop_loss_pct = max(0.015, (atr / current_price) * 1.0)  # 1.5-2.5%
                take_profit_pct = stop_loss_pct * 2.0  # 2:1 R/R (faster exits)

                logger.info(f"📈 MOMENTUM LONG for {symbol}: RSI {rsi:.1f}, Trend confirmed, Momentum {momentum_pct:.2f}%")

                return {
                    'direction': 'LONG',
                    'confidence': total_confidence,
                    'stop_loss_pct': stop_loss_pct,
                    'take_profit_pct': take_profit_pct,
                    'reason': f'Uptrend momentum: RSI={rsi:.1f}, EMA20>{ema_slow:.0f}, Mom={momentum_pct:.1f}%'
                }

            # === DOWNTREND MOMENTUM SHORT ===
            # LOOSENED: Enter when trend is DOWN - removed strict RSI and price filters
            # More aggressive for competition: catch the trend early
            if (trend_down and
                rsi < 55 and rsi > 22 and  # LOOSENED: from 45 to 55
                momentum_pct < -0.3):  # LOOSENED: from -1.0% to -0.3%

                base_confidence = min(0.45 + (55 - rsi) / 60, 0.80)  # Higher base confidence
                total_confidence = (base_confidence * 0.7) + (model_confidence * 0.3)

                # WIDENED stops for crypto volatility
                stop_loss_pct = max(0.015, (atr / current_price) * 1.0)  # 1.5-2.5%
                take_profit_pct = stop_loss_pct * 2.0  # 2:1 R/R (faster exits)

                logger.info(f"📉 MOMENTUM SHORT for {symbol}: RSI {rsi:.1f}, Trend confirmed, Momentum {momentum_pct:.2f}%")

                return {
                    'direction': 'SHORT',
                    'confidence': total_confidence,
                    'stop_loss_pct': stop_loss_pct,
                    'take_profit_pct': take_profit_pct,
                    'reason': f'Downtrend momentum: RSI={rsi:.1f}, EMA20<{ema_slow:.0f}, Mom={momentum_pct:.1f}%'
                }

            # === EXTREME REVERSAL (Rare, high conviction only) ===
            # Only take reversals at EXTREME levels with confirmation
            if rsi < 20 and momentum_pct < -5 and trend_down:
                logger.info(f"🔄 EXTREME REVERSAL LONG for {symbol}: RSI {rsi:.1f} extremely oversold")
                return {
                    'direction': 'LONG',
                    'confidence': 0.65,
                    'stop_loss_pct': 0.008,
                    'take_profit_pct': 0.02,
                    'reason': f'Extreme reversal: RSI={rsi:.1f} < 20'
                }

            if rsi > 80 and momentum_pct > 5 and trend_up:
                logger.info(f"🔄 EXTREME REVERSAL SHORT for {symbol}: RSI {rsi:.1f} extremely overbought")
                return {
                    'direction': 'SHORT',
                    'confidence': 0.65,
                    'stop_loss_pct': 0.008,
                    'take_profit_pct': 0.02,
                    'reason': f'Extreme reversal: RSI={rsi:.1f} > 80'
                }

            return None

        except Exception as e:
            logger.error(f"Error generating momentum signal for {symbol}: {e}")
            return None
