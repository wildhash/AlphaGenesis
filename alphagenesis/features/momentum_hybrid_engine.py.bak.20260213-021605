"""
Momentum Hybrid Engine - Competition Edition
Trend-following strategy with AI confirmation for WEEX AI Wars
"""
import os
import numpy as np
import time
from typing import Dict, Optional
from loguru import logger
from alphagenesis.sdm.semantic_binding import MarketRegime


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
        model_confidence: float = 0.6,
        regime: MarketRegime | None = None
    ) -> Optional[Dict]:
        """
        Generate MOMENTUM/TREND-FOLLOWING signal (NOT reversal).

        Strategy:
        - LONG: Uptrend confirmed (EMA20 > EMA50, RSI > 55, price > EMA20)
        - SHORT: Downtrend confirmed (EMA20 < EMA50, RSI < 45, price < EMA20)

        Returns signal dict or None
        """
        try:
            if regime is None:
                regime = MarketRegime.UNKNOWN
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
            logger.info(f"DIAG_MOMENTUM_LEN symbol={symbol} candles={len(closes)}")
            if len(closes) < 50:
                logger.info(f"DIAG_MOMENTUM_SHORT_CANDLES symbol={symbol} candles={len(closes)}")
                return None

            prices = np.array(closes)
            highs_arr = np.array(highs)
            lows_arr = np.array(lows)

            # Calculate indicators
            ema_fast = self._calculate_ema(prices, self.ema_fast)
            ema_slow = self._calculate_ema(prices, self.ema_slow)
            ema_long = self._calculate_ema(prices, 200)
            ema_fast_prev = self._calculate_ema(prices[:-1], self.ema_fast) if len(prices) > (self.ema_fast + 1) else ema_fast
            ema_fast_slope = ema_fast - ema_fast_prev
            rsi = self._calculate_rsi(prices)

            tr_list = []
            for i in range(1, len(prices)):
                high_low = highs_arr[i] - lows_arr[i]
                high_close = abs(highs_arr[i] - prices[i-1])
                low_close = abs(lows_arr[i] - prices[i-1])
                tr_list.append(max(high_low, high_close, low_close))

            def _atr_from_tr(period: int) -> float:
                if not tr_list:
                    return abs(highs_arr[-1] - lows_arr[-1])
                if len(tr_list) < period:
                    return float(np.mean(tr_list))
                return float(np.mean(tr_list[-period:]))

            atr = _atr_from_tr(14)
            atr_fast = _atr_from_tr(7)
            atr_slow = _atr_from_tr(21)
            atr_pct = (atr_fast / current_price * 100.0) if (current_price and atr_fast) else 0.0
            atr_pct_slow = (atr_slow / current_price * 100.0) if (current_price and atr_slow) else 0.0

            tr_recent = float(np.mean(tr_list[-3:])) if len(tr_list) >= 3 else 0.0
            tr_prev = float(np.mean(tr_list[-13:-3])) if len(tr_list) >= 13 else 0.0
            tr_expanding = tr_prev > 0 and tr_recent >= (tr_prev * 1.2)
            atr_rising = atr_pct > 0 and atr_pct >= max(atr_pct_slow * 1.15, 0.25)

            # Trend detection
            trend_up = ema_fast > ema_slow
            trend_down = ema_fast < ema_slow

            # Momentum (10-period rate of change)
            momentum_pct = ((prices[-1] - prices[-10]) / prices[-10]) * 100

            low_vol_flag = (regime == MarketRegime.LOW_VOLATILITY)
            logger.info(
                f"DIAG_MOMENTUM symbol={symbol} regime={regime} momentum_pct={momentum_pct:.4f} rsi={rsi:.2f} low_vol={low_vol_flag}"
            )

            # Soft LOW_VOL gate: allow only extreme impulse moves to avoid churn.
            if regime == MarketRegime.LOW_VOLATILITY:
                logger.info("LOW_VOL gate reached")
                allow = False
                if symbol in ("cmt_ethusdt", "cmt_solusdt"):
                    logger.info(
                        "SOFT_GATE_BLOCKED symbol={} reason=override_loss_leader",
                        symbol
                    )
                    logger.warning(
                        "SOFT_GATE_BLOCKED_HARD symbol={} entry_reason=LOW_VOL_EXTREME_OVERRIDE reason=permanent_eth_sol_block",
                        symbol,
                    )
                    return "no_signal"
                probe_override_symbols = {
                    s.strip().lower()
                    for s in os.getenv(
                        "PROBE_OVERRIDE_ALLOWLIST",
                        "cmt_bnbusdt,cmt_adausdt",
                    ).split(",")
                    if s.strip()
                }
                probe_mode_enabled = os.getenv("PROBE_MODE_ENABLED", "true").lower() == "true"
                probe_size_multiplier_raw = os.getenv("PROBE_SIZE_MULTIPLIER", "0.3")
                try:
                    probe_size_multiplier = float(probe_size_multiplier_raw)
                except (TypeError, ValueError):
                    probe_size_multiplier = 0.5
                probe_size_multiplier = max(0.05, min(1.0, probe_size_multiplier))
                extreme_thresholds = {
                    'cmt_bnbusdt': 1.2,
                    'cmt_adausdt': 1.3,
                }
                extreme_threshold = extreme_thresholds.get(symbol)
                if atr_pct < 0.20:
                    vol_bucket = "VERY_LOW_VOL"
                elif atr_pct < 0.40:
                    vol_bucket = "LOW_VOL"
                elif atr_pct < 0.80:
                    vol_bucket = "MID_VOL"
                else:
                    vol_bucket = "HIGH_VOL"
                if extreme_threshold and probe_mode_enabled and symbol in probe_override_symbols:
                    if abs(momentum_pct) >= extreme_threshold and atr_rising and tr_expanding:
                        allow_long = trend_up or (
                            current_price > ema_slow and current_price > ema_fast and rsi > 55
                        )
                        allow_short = trend_down or (
                            current_price < ema_slow and current_price < ema_fast and rsi < 45
                        )
                        atr_ratio = (atr_pct / atr_pct_slow) if atr_pct_slow > 0 else None
                        thresholds = {
                            "momentum_abs_min": extreme_threshold,
                            "rsi_long_max": 75.0,
                            "rsi_short_min": 25.0,
                            "atr_rising_min_ratio": 1.15,
                            "tr_expanding_min_ratio": 1.2,
                        }
                        base_gates = {
                            "low_vol_bypassed": True,
                            "probe_mode": True,
                            "momentum_gate": abs(momentum_pct) >= extreme_threshold,
                            "atr_rising": atr_rising,
                            "tr_expanding": tr_expanding,
                            "allow_long": allow_long,
                            "allow_short": allow_short,
                        }

                        entry_features = {
                            'momentum_pct': momentum_pct,
                            'atr_pct': atr_pct,
                            'atr_pct_slow': atr_pct_slow,
                            'atr_ratio': atr_ratio,
                            'rsi': rsi,
                            'price': current_price,
                            'ema20': ema_fast,
                            'ema50': ema_slow,
                            'ema200': ema_long,
                            'ema20_slope': ema_fast_slope,
                            'price_gt_ema50': current_price > ema_slow,
                        }

                        if momentum_pct > 0 and allow_long and rsi < 75:
                            logger.info(
                                "DIAG_EXTREME_OVERRIDE symbol={} momentum_pct={:.3f} atr_pct={:.3f} rsi={:.1f} trend_up={} trend_down={} decision=ALLOW_LONG",
                                symbol,
                                momentum_pct,
                                atr_pct,
                                rsi,
                                trend_up,
                                trend_down
                            )
                            logger.info(
                                "PROBE_MODE=1 symbol={} entry_reason=LOW_VOL_EXTREME_OVERRIDE side=LONG allowlist={}",
                                symbol,
                                sorted(probe_override_symbols),
                            )
                            stop_loss_pct = max(0.005, (atr / current_price) * 0.6)
                            take_profit_pct = stop_loss_pct * 2.5
                            reversal_aligned = (not trend_up) and allow_long
                            entry_gates = dict(base_gates)
                            entry_gates["reversal_aligned"] = reversal_aligned
                            return {
                                'direction': 'LONG',
                                'confidence': 0.72,
                                'stop_loss_pct': stop_loss_pct,
                                'take_profit_pct': take_profit_pct,
                                'reason': 'LOW_VOL_EXTREME_OVERRIDE',
                                'features': entry_features,
                                'entry_meta': {
                                    'entry_reason': 'LOW_VOL_EXTREME_OVERRIDE',
                                    'symbol': symbol,
                                    'ts': time.time(),
                                    'side': 'LONG',
                                    'probe_mode': True,
                                    'probe_symbol_allowlist': sorted(probe_override_symbols),
                                    'probe_size_multiplier': probe_size_multiplier,
                                    'vol_bucket': vol_bucket,
                                    'atr_ratio': atr_ratio,
                                    'features': entry_features,
                                    'thresholds': thresholds,
                                    'gates': entry_gates,
                                },
                                'probe_mode': True,
                                'probe_symbol_allowlist': sorted(probe_override_symbols),
                                'probe_size_multiplier': probe_size_multiplier,
                            }
                        if momentum_pct < 0 and allow_short and rsi > 25:
                            logger.info(
                                "DIAG_EXTREME_OVERRIDE symbol={} momentum_pct={:.3f} atr_pct={:.3f} rsi={:.1f} trend_up={} trend_down={} decision=ALLOW_SHORT",
                                symbol,
                                momentum_pct,
                                atr_pct,
                                rsi,
                                trend_up,
                                trend_down
                            )
                            logger.info(
                                "PROBE_MODE=1 symbol={} entry_reason=LOW_VOL_EXTREME_OVERRIDE side=SHORT allowlist={}",
                                symbol,
                                sorted(probe_override_symbols),
                            )
                            stop_loss_pct = max(0.005, (atr / current_price) * 0.6)
                            take_profit_pct = stop_loss_pct * 2.5
                            reversal_aligned = (not trend_down) and allow_short
                            entry_gates = dict(base_gates)
                            entry_gates["reversal_aligned"] = reversal_aligned
                            return {
                                'direction': 'SHORT',
                                'confidence': 0.72,
                                'stop_loss_pct': stop_loss_pct,
                                'take_profit_pct': take_profit_pct,
                                'reason': 'LOW_VOL_EXTREME_OVERRIDE',
                                'features': entry_features,
                                'entry_meta': {
                                    'entry_reason': 'LOW_VOL_EXTREME_OVERRIDE',
                                    'symbol': symbol,
                                    'ts': time.time(),
                                    'side': 'SHORT',
                                    'probe_mode': True,
                                    'probe_symbol_allowlist': sorted(probe_override_symbols),
                                    'probe_size_multiplier': probe_size_multiplier,
                                    'vol_bucket': vol_bucket,
                                    'atr_ratio': atr_ratio,
                                    'features': entry_features,
                                    'thresholds': thresholds,
                                    'gates': entry_gates,
                                },
                                'probe_mode': True,
                                'probe_symbol_allowlist': sorted(probe_override_symbols),
                                'probe_size_multiplier': probe_size_multiplier,
                            }
                elif extreme_threshold and not probe_mode_enabled:
                    logger.info(
                        "SOFT_GATE_PROBE_SKIP symbol={} reason=probe_mode_disabled",
                        symbol,
                    )
                elif extreme_threshold and symbol not in probe_override_symbols:
                    logger.info(
                        "SOFT_GATE_PROBE_SKIP symbol={} reason=not_in_probe_allowlist allowlist={}",
                        symbol,
                        sorted(probe_override_symbols),
                    )

                # LOW_VOL_SHORT_GATE_X3_WITH_ATR: conservative short unlock w/ range expansion confirmation
                if momentum_pct <= -3.0 and rsi <= 45 and atr_pct >= 0.25:
                    return {
                        'direction': 'SHORT',
                        'confidence': 0.68,
                        'stop_loss_pct': 0.008,
                        'take_profit_pct': 0.02,
                        'reason': 'LOW_VOL_SHORT_GATE_X3_WITH_ATR'
                    }
                if momentum_pct <= -3.0 and rsi <= 45 and atr_pct < 0.25:
                    logger.info(
                        f"LOW_VOL_SHORT_GATE_X3_WITH_ATR blocked symbol={symbol} momentum_pct={momentum_pct:.2f} rsi={rsi:.1f} atr_pct={atr_pct:.3f}"
                    )
                long_threshold = 2.0
                short_threshold = -1.5
                if momentum_pct > long_threshold:
                    allow = True
                elif momentum_pct < short_threshold:
                    allow = True
                if allow:
                    logger.info(
                        f"SOFT_GATE_LOW_VOL_PASS symbol={symbol} momentum_pct={momentum_pct:.3f} thresholds=[{short_threshold:.3f},{long_threshold:.3f}]"
                    )
                if not allow:
                    logger.info(f"LOW_VOL gate blocked: momentum_pct={momentum_pct:.3f} rsi={rsi:.1f} trend_up={trend_up} trend_down={trend_down}")

                    return "no_signal"

            logger.info(f"{symbol} - RSI: {rsi:.1f}, EMA20: {ema_fast:.2f}, EMA50: {ema_slow:.2f}, Momentum: {momentum_pct:.2f}%")
            # === Regime-Segmented Momentum Thresholds ===
            if regime == MarketRegime.STRONG_UPTREND:
                long_momentum_threshold = 0.4
                short_momentum_threshold = -0.5
            elif regime == MarketRegime.STRONG_DOWNTREND:
                long_momentum_threshold = 0.7
                short_momentum_threshold = -0.4
            else:
                long_momentum_threshold = 0.7
                short_momentum_threshold = -0.5
            # === End Regime-Segmented Thresholds ===


            # === UPTREND MOMENTUM LONG ===
            # Enter when trend is UP and RSI confirms strength (not overbought yet)
            if (trend_up and
                rsi > 52 and rsi < 75 and  # Strong but not extreme
                current_price > ema_fast and
                momentum_pct > long_momentum_threshold):  # Positive momentum

                # Confidence scales with signal strength
                base_confidence = min(0.4 + (rsi - 55) / 50, 0.75)
                total_confidence = (base_confidence * 0.7) + (model_confidence * 0.3)

                # Dynamic risk based on ATR
                stop_loss_pct = max(0.005, (atr / current_price) * 0.6)  # 0.5-1%
                take_profit_pct = stop_loss_pct * 2.5  # 2.5:1 R/R

                logger.info(f"📈 MOMENTUM LONG for {symbol}: RSI {rsi:.1f}, Trend confirmed, Momentum {momentum_pct:.2f}%")

                return {
                    'direction': 'LONG',
                    'confidence': total_confidence,
                    'stop_loss_pct': stop_loss_pct,
                    'take_profit_pct': take_profit_pct,
                    'reason': f'Uptrend momentum: RSI={rsi:.1f}, EMA20>{ema_slow:.0f}, Mom={momentum_pct:.1f}%'
                }

            # === DOWNTREND MOMENTUM SHORT ===
            # Enter when trend is DOWN and RSI confirms weakness (not oversold yet)
            if (trend_down and
                rsi < 45 and rsi > 25 and  # Weak but not extreme
                current_price < ema_fast and
                momentum_pct < short_momentum_threshold):  # Negative momentum (slightly relaxed)

                base_confidence = min(0.4 + (45 - rsi) / 50, 0.75)
                total_confidence = (base_confidence * 0.7) + (model_confidence * 0.3)

                stop_loss_pct = max(0.005, (atr / current_price) * 0.6)
                take_profit_pct = stop_loss_pct * 2.5

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
            # Patch B: block knife-catch longs in strong downtrend
            if regime == MarketRegime.STRONG_DOWNTREND and rsi < 20 and momentum_pct <= -0.25:
                logger.info(
                    f"BLOCK_EXTREME_REVERSAL_LONG_STRONG_DOWNTREND symbol={symbol} rsi={rsi:.1f} momentum_pct={momentum_pct:.3f}"
                )
                return "no_signal"

            if rsi < 20 and momentum_pct < -5:
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
