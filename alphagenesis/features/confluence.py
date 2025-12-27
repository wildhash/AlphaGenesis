"""
Multi-Timeframe Confluence Module

Calculates confluence scores across multiple timeframes to identify
high-probability trade setups.

Key insight from DeepSeek's Alpha Arena success:
Only trade when multiple timeframes agree on direction.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
from loguru import logger


class TrendDirection(Enum):
    """Trend direction for a timeframe."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class TimeframeAnalysis:
    """Analysis result for a single timeframe."""
    timeframe: str
    direction: TrendDirection
    strength: float  # 0-1
    ema_fast: float
    ema_slow: float
    rsi: float
    macd_histogram: float


@dataclass
class ConfluenceResult:
    """Multi-timeframe confluence analysis result."""
    overall_direction: TrendDirection
    confluence_score: float  # 0-1
    bullish_count: int
    bearish_count: int
    neutral_count: int
    timeframe_analyses: List[TimeframeAnalysis]
    recommendation: str


class MultiTimeframeConfluence:
    """
    Calculates multi-timeframe confluence for trade validation.
    
    Confluence Score:
    - 1.0 = All timeframes strongly agree
    - 0.7+ = Strong agreement (tradeable)
    - 0.5 = Mixed signals (avoid)
    - 0.3- = Conflicting signals (stay out)
    """
    
    # Default timeframes to analyze
    DEFAULT_TIMEFRAMES = ['5m', '15m', '1h', '4h', '1d']
    
    # Minimum confluence to approve trade
    MIN_CONFLUENCE_THRESHOLD = 0.7
    
    def __init__(
        self,
        timeframes: Optional[List[str]] = None,
        min_confluence: float = 0.7,
        ema_fast_period: int = 8,
        ema_slow_period: int = 21,
    ):
        """
        Initialize confluence analyzer.
        
        Args:
            timeframes: List of timeframes to analyze
            min_confluence: Minimum score for trade approval
            ema_fast_period: Fast EMA period
            ema_slow_period: Slow EMA period
        """
        self.timeframes = timeframes or self.DEFAULT_TIMEFRAMES
        self.min_confluence = min_confluence
        self.ema_fast_period = ema_fast_period
        self.ema_slow_period = ema_slow_period
        
        logger.info(f"MultiTimeframeConfluence initialized: {self.timeframes}")
    
    def calculate_confluence(
        self,
        price_data: Dict[str, np.ndarray]
    ) -> ConfluenceResult:
        """
        Calculate confluence across all timeframes.
        
        Args:
            price_data: Dict mapping timeframe to price array
                       e.g., {'1h': np.array([...]), '4h': np.array([...])}
        
        Returns:
            ConfluenceResult with overall score and breakdown
        """
        analyses = []
        bullish = 0
        bearish = 0
        neutral = 0
        
        for tf in self.timeframes:
            prices = price_data.get(tf)
            
            if prices is None or len(prices) < self.ema_slow_period + 10:
                continue
            
            analysis = self._analyze_timeframe(tf, np.array(prices))
            analyses.append(analysis)
            
            if analysis.direction == TrendDirection.BULLISH:
                bullish += 1
            elif analysis.direction == TrendDirection.BEARISH:
                bearish += 1
            else:
                neutral += 1
        
        total = len(analyses)
        if total == 0:
            return ConfluenceResult(
                overall_direction=TrendDirection.NEUTRAL,
                confluence_score=0.0,
                bullish_count=0,
                bearish_count=0,
                neutral_count=0,
                timeframe_analyses=[],
                recommendation="Insufficient data"
            )
        
        # Calculate confluence score
        max_agreement = max(bullish, bearish)
        confluence_score = max_agreement / total
        
        # Adjust for neutrals (they reduce confidence)
        if neutral > 0:
            confluence_score *= (1 - neutral / (total * 2))
        
        # Determine overall direction
        if bullish > bearish and confluence_score >= self.min_confluence:
            overall_direction = TrendDirection.BULLISH
            recommendation = f"BULLISH - {bullish}/{total} timeframes agree"
        elif bearish > bullish and confluence_score >= self.min_confluence:
            overall_direction = TrendDirection.BEARISH
            recommendation = f"BEARISH - {bearish}/{total} timeframes agree"
        else:
            overall_direction = TrendDirection.NEUTRAL
            recommendation = f"NEUTRAL - Mixed signals ({bullish}B/{bearish}S/{neutral}N)"
        
        return ConfluenceResult(
            overall_direction=overall_direction,
            confluence_score=confluence_score,
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            timeframe_analyses=analyses,
            recommendation=recommendation
        )

    def _analyze_timeframe(self, timeframe: str, prices: np.ndarray) -> TimeframeAnalysis:
        """
        Analyze a single timeframe for trend direction.
        
        Uses:
        - EMA crossover
        - RSI
        - MACD histogram
        """
        # Calculate indicators
        ema_fast = self._ema(prices, self.ema_fast_period)
        ema_slow = self._ema(prices, self.ema_slow_period)
        rsi = self._rsi(prices, 14)
        macd_hist = self._macd_histogram(prices)
        
        # Determine direction based on multiple factors
        bullish_signals = 0
        bearish_signals = 0
        
        # EMA crossover
        if ema_fast[-1] > ema_slow[-1]:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # EMA slope
        ema_fast_slope = (ema_fast[-1] - ema_fast[-3]) / ema_fast[-3]
        if ema_fast_slope > 0.001:
            bullish_signals += 1
        elif ema_fast_slope < -0.001:
            bearish_signals += 1
        
        # RSI
        if rsi > 50:
            bullish_signals += 0.5
        elif rsi < 50:
            bearish_signals += 0.5
        
        # MACD histogram
        if macd_hist > 0:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # Determine overall direction
        if bullish_signals > bearish_signals + 1:
            direction = TrendDirection.BULLISH
            strength = bullish_signals / (bullish_signals + bearish_signals)
        elif bearish_signals > bullish_signals + 1:
            direction = TrendDirection.BEARISH
            strength = bearish_signals / (bullish_signals + bearish_signals)
        else:
            direction = TrendDirection.NEUTRAL
            strength = 0.5
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            direction=direction,
            strength=strength,
            ema_fast=ema_fast[-1],
            ema_slow=ema_slow[-1],
            rsi=rsi,
            macd_histogram=macd_hist
        )
    
    def _ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        alpha = 2 / (period + 1)
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        return ema
    
    def _rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI."""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _macd_histogram(
        self, 
        prices: np.ndarray,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> float:
        """Calculate MACD histogram."""
        ema_fast = self._ema(prices, fast)
        ema_slow = self._ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self._ema(macd_line, signal)
        histogram = macd_line - signal_line
        return histogram[-1]
    
    def is_tradeable(self, result: ConfluenceResult) -> bool:
        """Check if confluence is strong enough for trading."""
        return (
            result.confluence_score >= self.min_confluence and
            result.overall_direction != TrendDirection.NEUTRAL
        )
    
    def get_trade_bias(self, result: ConfluenceResult) -> str:
        """Get recommended trade direction."""
        if not self.is_tradeable(result):
            return "HOLD"
        return "LONG" if result.overall_direction == TrendDirection.BULLISH else "SHORT"


__all__ = [
    'MultiTimeframeConfluence',
    'ConfluenceResult',
    'TimeframeAnalysis',
    'TrendDirection'
]
