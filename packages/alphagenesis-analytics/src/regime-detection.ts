/**
 * Market Regime Detection Module
 * Adapted from AlphaGenesis features module (alphagenesis/features/market_regime.py)
 * 
 * Simplified market regime detection for UI/frontend use.
 * Classifies markets as calm, trending, or volatile based on heuristics.
 * 
 * Note: For production trading, use the full Python implementation with
 * Hidden Markov Models and advanced statistical methods.
 */

export type MarketRegime = 'calm' | 'trending' | 'volatile';

export interface RegimeDetectionResult {
  regime: MarketRegime;
  confidence: number; // 0-1
  trendStrength: number; // -1 to 1 (negative = bearish, positive = bullish)
  volatilityPercentile: number; // 0-100
  factors: string[];
}

export interface RegimeThresholds {
  highVolatilityPercentile: number;
  strongTrendThreshold: number;
  trendLookback: number;
  volatilityLookback: number;
}

const DEFAULT_THRESHOLDS: RegimeThresholds = {
  highVolatilityPercentile: 80,
  strongTrendThreshold: 0.02,
  trendLookback: 50,
  volatilityLookback: 20,
};

/**
 * Detect market regime from price and volume data
 * Adapted from MarketRegimeDetector.detect_regime in market_regime.py
 * 
 * @param prices - Array of closing prices (most recent last)
 * @param volume - Optional array of volumes
 * @param thresholds - Optional regime detection thresholds
 * @returns Regime detection result
 */
export function detectRegime(
  prices: number[],
  volume?: number[],
  thresholds: Partial<RegimeThresholds> = {}
): RegimeDetectionResult {
  const config = { ...DEFAULT_THRESHOLDS, ...thresholds };

  if (prices.length < Math.max(config.trendLookback, config.volatilityLookback)) {
    return {
      regime: 'calm',
      confidence: 0,
      trendStrength: 0,
      volatilityPercentile: 50,
      factors: ['Insufficient data'],
    };
  }

  // Analyze trend and volatility
  const trendInfo = analyzeTrend(prices, config.trendLookback);
  const volatilityInfo = analyzeVolatility(prices, config.volatilityLookback);

  const factors: string[] = [];
  let regime: MarketRegime = 'calm';
  let confidence = 0;

  // Determine regime based on volatility and trend
  if (volatilityInfo.percentile > config.highVolatilityPercentile) {
    regime = 'volatile';
    confidence = volatilityInfo.percentile / 100;
    factors.push(`High volatility (${volatilityInfo.percentile.toFixed(0)}th percentile)`);
  } else if (Math.abs(trendInfo.strength) > config.strongTrendThreshold) {
    regime = 'trending';
    confidence = Math.min(Math.abs(trendInfo.strength) / 0.05, 1);
    factors.push(
      ...trendInfo.factors,
      `${trendInfo.strength > 0 ? 'Bullish' : 'Bearish'} trend (strength: ${trendInfo.strength.toFixed(3)})`
    );
  } else {
    regime = 'calm';
    confidence = 1 - Math.abs(trendInfo.strength) / config.strongTrendThreshold;
    factors.push('No strong trend or volatility');
  }

  return {
    regime,
    confidence,
    trendStrength: trendInfo.strength,
    volatilityPercentile: volatilityInfo.percentile,
    factors,
  };
}

/**
 * Analyze trend strength using EMAs and price patterns
 * Adapted from MarketRegimeDetector._analyze_trend in market_regime.py
 */
function analyzeTrend(
  prices: number[],
  lookback: number
): { strength: number; factors: string[] } {
  const factors: string[] = [];
  const scores: number[] = [];

  // Calculate EMAs
  const ema20 = calculateEMA(prices, 20);
  const ema50 = calculateEMA(prices, 50);

  if (ema20.length < 10 || ema50.length < 10) {
    return { strength: 0, factors: ['Insufficient data for EMA'] };
  }

  // EMA slopes
  const ema20Slope =
    ema20[ema20.length - 5] !== 0
      ? (ema20[ema20.length - 1] - ema20[ema20.length - 5]) / ema20[ema20.length - 5]
      : 0;
  const ema50Slope =
    ema50[ema50.length - 10] !== 0
      ? (ema50[ema50.length - 1] - ema50[ema50.length - 10]) / ema50[ema50.length - 10]
      : 0;

  scores.push(ema20Slope * 2); // Weight recent trend more
  scores.push(ema50Slope);

  if (ema20Slope > 0.01) {
    factors.push(`EMA20 rising (${(ema20Slope * 100).toFixed(2)}%)`);
  } else if (ema20Slope < -0.01) {
    factors.push(`EMA20 falling (${(ema20Slope * 100).toFixed(2)}%)`);
  }

  // Price position relative to EMAs
  const currentPrice = prices[prices.length - 1];
  const priceVsEma20 =
    ema20[ema20.length - 1] !== 0
      ? (currentPrice - ema20[ema20.length - 1]) / ema20[ema20.length - 1]
      : 0;
  const priceVsEma50 =
    ema50[ema50.length - 1] !== 0
      ? (currentPrice - ema50[ema50.length - 1]) / ema50[ema50.length - 1]
      : 0;

  scores.push(priceVsEma20);
  scores.push(priceVsEma50 * 0.5);

  // Check EMA alignment
  if (
    currentPrice > ema20[ema20.length - 1] &&
    ema20[ema20.length - 1] > ema50[ema50.length - 1]
  ) {
    factors.push('Bullish EMA alignment (Price > EMA20 > EMA50)');
  } else if (
    currentPrice < ema20[ema20.length - 1] &&
    ema20[ema20.length - 1] < ema50[ema50.length - 1]
  ) {
    factors.push('Bearish EMA alignment (Price < EMA20 < EMA50)');
  }

  // Higher highs / Lower lows
  const recent10 = prices.slice(-10);
  const prev10 = prices.slice(-20, -10);

  if (recent10.length === 10 && prev10.length === 10) {
    const recentHigh = Math.max(...recent10);
    const prevHigh = Math.max(...prev10);
    const recentLow = Math.min(...recent10);
    const prevLow = Math.min(...prev10);

    if (recentHigh > prevHigh && recentLow > prevLow) {
      factors.push('Higher highs & higher lows');
      scores.push(0.02);
    } else if (recentHigh < prevHigh && recentLow < prevLow) {
      factors.push('Lower highs & lower lows');
      scores.push(-0.02);
    }
  }

  // Combined trend strength
  const strength =
    scores.length > 0
      ? Math.max(-1, Math.min(1, scores.reduce((sum, s) => sum + s, 0) / scores.length))
      : 0;

  return { strength, factors };
}

/**
 * Analyze volatility relative to historical levels
 */
function analyzeVolatility(
  prices: number[],
  lookback: number
): { current: number; percentile: number } {
  // Calculate returns
  const returns: number[] = [];
  for (let i = 1; i < prices.length; i++) {
    if (prices[i - 1] !== 0) {
      returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
    }
  }

  // Current volatility (last lookback periods)
  const recentReturns = returns.slice(-lookback);
  const mean = recentReturns.reduce((sum, r) => sum + r, 0) / recentReturns.length;
  const variance =
    recentReturns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) /
    recentReturns.length;
  const currentVol = Math.sqrt(variance) * Math.sqrt(252); // Annualized

  // Calculate historical volatility for percentile
  const historicalVols: number[] = [];
  for (let i = lookback; i < returns.length; i += lookback) {
    const window = returns.slice(i - lookback, i);
    const windowMean = window.reduce((sum, r) => sum + r, 0) / window.length;
    const windowVar =
      window.reduce((sum, r) => sum + Math.pow(r - windowMean, 2), 0) / window.length;
    historicalVols.push(Math.sqrt(windowVar) * Math.sqrt(252));
  }

  // Calculate percentile
  let percentile = 50;
  if (historicalVols.length > 0) {
    const sorted = [...historicalVols].sort((a, b) => a - b);
    const rank = sorted.findIndex((v) => v >= currentVol);
    percentile = rank >= 0 ? (rank / sorted.length) * 100 : 100;
  }

  return { current: currentVol, percentile };
}

/**
 * Calculate Exponential Moving Average
 */
function calculateEMA(prices: number[], period: number): number[] {
  if (prices.length < period) {
    return [];
  }

  const alpha = 2 / (period + 1);
  const ema: number[] = new Array(prices.length);
  ema[0] = prices[0];

  for (let i = 1; i < prices.length; i++) {
    ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1];
  }

  return ema;
}

/**
 * Check if current regime is suitable for trading
 * Based on AlphaGenesis strategy: prefer trending markets
 * 
 * @param result - Regime detection result
 * @returns True if suitable for trading
 */
export function isTradeable(result: RegimeDetectionResult): boolean {
  return result.regime === 'trending' && result.confidence > 0.6;
}

/**
 * Get regime classification for display
 */
export function getRegimeLabel(regime: MarketRegime): string {
  const labels: Record<MarketRegime, string> = {
    calm: 'Calm/Ranging',
    trending: 'Trending',
    volatile: 'High Volatility',
  };
  return labels[regime];
}
