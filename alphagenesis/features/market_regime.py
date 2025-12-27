"""
Market Regime Detection Module

Advanced market regime classification using multiple methods:
1. Volatility Regime (ATR percentile)
2. Trend Regime (EMA slopes and positions)
3. Hidden Markov Model (optional advanced)

This module helps the system adapt strategy to market conditions:
- Trending markets: Follow momentum, use trailing stops
- Ranging markets: Mean reversion, tighter stops
- High volatility: Reduce size, wider stops
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
import numpy as np
from loguru import logger


class RegimeType(Enum):
    """Market regime classifications."""
    STRONG_BULL = "strong_bull"
    WEAK_BULL = "weak_bull"
    RANGING = "ranging"
    WEAK_BEAR = "weak_bear"
    STRONG_BEAR = "strong_bear"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class RegimeState:
    """Current regime state with confidence."""
    regime: RegimeType
    confidence: float  # 0-1
    trend_strength: float  # -1 to 1
    volatility_percentile: float  # 0-100
    supporting_factors: List[str]


class MarketRegimeDetector:
    """
    Detects the current market regime to adapt trading strategy.
    
    Key insight from DeepSeek's success: Only trade in strong trending regimes.
    """
    
    def __init__(
        self,
        trend_lookback: int = 50,
        volatility_lookback: int = 20,
        strong_trend_threshold: float = 0.02,
        high_vol_percentile: float = 80,
    ):
        """
        Initialize regime detector.
        
        Args:
            trend_lookback: Periods for trend calculation
            volatility_lookback: Periods for volatility calculation
            strong_trend_threshold: Minimum slope for strong trend
            high_vol_percentile: Percentile threshold for high volatility
        """
        self.trend_lookback = trend_lookback
        self.volatility_lookback = volatility_lookback
        self.strong_trend_threshold = strong_trend_threshold
        self.high_vol_percentile = high_vol_percentile
        
        # Historical volatility for percentile calculation
        self.volatility_history: List[float] = []
        
        logger.info(f"MarketRegimeDetector initialized")
    
    def detect_regime(self, prices: np.ndarray, volumes: Optional[np.ndarray] = None) -> RegimeState:
        """
        Detect current market regime from price data.
        
        Args:
            prices: Array of closing prices (most recent last)
            volumes: Optional volume data
            
        Returns:
            RegimeState with classification and confidence
        """
        if len(prices) < max(self.trend_lookback, self.volatility_lookback):
            return RegimeState(
                regime=RegimeType.RANGING,
                confidence=0.0,
                trend_strength=0.0,
                volatility_percentile=50.0,
                supporting_factors=["Insufficient data"]
            )
        
        prices = np.array(prices)
        
        # Calculate components
        trend_info = self._analyze_trend(prices)
        volatility_info = self._analyze_volatility(prices)
        
        supporting_factors = []
        
        # Determine regime
        if volatility_info['percentile'] > self.high_vol_percentile:
            regime = RegimeType.HIGH_VOLATILITY
            confidence = volatility_info['percentile'] / 100
            supporting_factors.append(f"Volatility at {volatility_info['percentile']:.0f}th percentile")
        elif volatility_info['percentile'] < 20:
            regime = RegimeType.LOW_VOLATILITY
            confidence = (100 - volatility_info['percentile']) / 100
            supporting_factors.append(f"Volatility at {volatility_info['percentile']:.0f}th percentile")
        elif trend_info['strength'] > self.strong_trend_threshold:
            regime = RegimeType.STRONG_BULL
            confidence = min(trend_info['strength'] / 0.05, 1.0)
            supporting_factors.extend(trend_info['factors'])
        elif trend_info['strength'] > 0.005:
            regime = RegimeType.WEAK_BULL
            confidence = trend_info['strength'] / self.strong_trend_threshold
            supporting_factors.extend(trend_info['factors'])
        elif trend_info['strength'] < -self.strong_trend_threshold:
            regime = RegimeType.STRONG_BEAR
            confidence = min(abs(trend_info['strength']) / 0.05, 1.0)
            supporting_factors.extend(trend_info['factors'])
        elif trend_info['strength'] < -0.005:
            regime = RegimeType.WEAK_BEAR
            confidence = abs(trend_info['strength']) / self.strong_trend_threshold
            supporting_factors.extend(trend_info['factors'])
        else:
            regime = RegimeType.RANGING
            confidence = 1.0 - abs(trend_info['strength']) / self.strong_trend_threshold
            supporting_factors.append("No clear trend direction")
        
        return RegimeState(
            regime=regime,
            confidence=confidence,
            trend_strength=trend_info['strength'],
            volatility_percentile=volatility_info['percentile'],
            supporting_factors=supporting_factors
        )

    def _analyze_trend(self, prices: np.ndarray) -> Dict[str, Any]:
        """
        Analyze trend using multiple indicators.
        
        Returns:
            Dict with 'strength' (-1 to 1) and 'factors' list
        """
        factors = []
        scores = []
        
        # EMA analysis
        ema_20 = self._ema(prices, 20)
        ema_50 = self._ema(prices, 50)
        
        # EMA slopes
        ema_20_slope = (ema_20[-1] - ema_20[-5]) / ema_20[-5] if ema_20[-5] != 0 else 0
        ema_50_slope = (ema_50[-1] - ema_50[-10]) / ema_50[-10] if ema_50[-10] != 0 else 0
        
        scores.append(ema_20_slope * 2)  # Weight recent trend more
        scores.append(ema_50_slope)
        
        if ema_20_slope > 0.01:
            factors.append(f"EMA20 rising ({ema_20_slope:.2%})")
        elif ema_20_slope < -0.01:
            factors.append(f"EMA20 falling ({ema_20_slope:.2%})")
        
        # Price position relative to EMAs
        current_price = prices[-1]
        price_vs_ema20 = (current_price - ema_20[-1]) / ema_20[-1]
        price_vs_ema50 = (current_price - ema_50[-1]) / ema_50[-1]
        
        scores.append(price_vs_ema20)
        scores.append(price_vs_ema50 * 0.5)
        
        if current_price > ema_20[-1] > ema_50[-1]:
            factors.append("Price > EMA20 > EMA50 (bullish alignment)")
        elif current_price < ema_20[-1] < ema_50[-1]:
            factors.append("Price < EMA20 < EMA50 (bearish alignment)")
        
        # Higher highs / Lower lows
        recent_high = np.max(prices[-10:])
        prev_high = np.max(prices[-20:-10])
        recent_low = np.min(prices[-10:])
        prev_low = np.min(prices[-20:-10])
        
        if recent_high > prev_high and recent_low > prev_low:
            factors.append("Higher highs & higher lows")
            scores.append(0.02)
        elif recent_high < prev_high and recent_low < prev_low:
            factors.append("Lower highs & lower lows")
            scores.append(-0.02)
        
        # Combined trend strength
        trend_strength = np.mean(scores) if scores else 0
        trend_strength = np.clip(trend_strength, -1, 1)
        
        return {
            'strength': trend_strength,
            'factors': factors
        }
    
    def _analyze_volatility(self, prices: np.ndarray) -> Dict[str, Any]:
        """
        Analyze current volatility relative to history.
        """
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        # Current volatility (std of recent returns)
        current_vol = np.std(returns[-self.volatility_lookback:]) * np.sqrt(252)  # Annualized
        
        # Update history
        self.volatility_history.append(current_vol)
        if len(self.volatility_history) > 1000:
            self.volatility_history = self.volatility_history[-1000:]
        
        # Calculate percentile
        if len(self.volatility_history) > 20:
            percentile = np.percentile(
                sorted(self.volatility_history),
                np.searchsorted(sorted(self.volatility_history), current_vol) / 
                len(self.volatility_history) * 100
            )
        else:
            percentile = 50.0  # Default to median
        
        return {
            'current': current_vol,
            'percentile': percentile
        }
    
    def _ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        alpha = 2 / (period + 1)
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        return ema
    
    def get_tradeable_regimes(self) -> List[RegimeType]:
        """Return list of regimes suitable for trading."""
        return [RegimeType.STRONG_BULL, RegimeType.STRONG_BEAR]
    
    def is_tradeable(self, regime_state: RegimeState) -> bool:
        """Check if current regime is suitable for trading."""
        return regime_state.regime in self.get_tradeable_regimes()


__all__ = ['MarketRegimeDetector', 'RegimeType', 'RegimeState']
