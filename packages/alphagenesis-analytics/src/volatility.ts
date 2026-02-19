/**
 * Volatility Analysis Module
 * Adapted from AlphaGenesis risk module (alphagenesis/risk/garch_model.py)
 * 
 * Provides TypeScript implementations of volatility calculations:
 * - Historical volatility
 * - Rolling volatility
 * - Annualized volatility
 * - Beta calculation
 * 
 * Note: This is simplified for UI use. Full GARCH models remain in Python.
 */

import { calculateReturns } from './utils';

export interface VolatilityMetrics {
  current: number;
  annualized: number;
  percentile: number;
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface BetaResult {
  beta: number;
  correlation: number;
  rSquared: number;
}

/**
 * Calculate historical volatility (standard deviation of returns)
 * Adapted from GARCH model concepts in garch_model.py
 * 
 * @param returns - Array of returns
 * @returns Standard deviation of returns
 */
export function calculateVolatility(returns: number[]): number {
  if (returns.length === 0) {
    return 0;
  }

  const validReturns = returns.filter((r) => !isNaN(r) && isFinite(r));

  if (validReturns.length === 0) {
    return 0;
  }

  const mean = validReturns.reduce((sum, r) => sum + r, 0) / validReturns.length;
  const variance =
    validReturns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) /
    validReturns.length;

  return Math.sqrt(variance);
}

/**
 * Calculate rolling volatility over a window
 * 
 * @param returns - Array of returns
 * @param windowSize - Size of rolling window (default: 20)
 * @returns Array of rolling volatility values
 */
export function calculateRollingVolatility(
  returns: number[],
  windowSize: number = 20
): number[] {
  if (returns.length < windowSize) {
    return [];
  }

  const rollingVol: number[] = [];

  for (let i = windowSize - 1; i < returns.length; i++) {
    const window = returns.slice(i - windowSize + 1, i + 1);
    rollingVol.push(calculateVolatility(window));
  }

  return rollingVol;
}

/**
 * Annualize volatility
 * 
 * @param volatility - Period volatility
 * @param periodsPerYear - Number of periods per year (default: 252 for daily)
 * @returns Annualized volatility
 */
export function annualizeVolatility(
  volatility: number,
  periodsPerYear: number = 252
): number {
  return volatility * Math.sqrt(periodsPerYear);
}

/**
 * Calculate volatility metrics with percentile and trend
 * 
 * @param returns - Array of returns
 * @param windowSize - Window size for rolling calculation
 * @returns Volatility metrics
 */
export function calculateVolatilityMetrics(
  returns: number[],
  windowSize: number = 20
): VolatilityMetrics {
  const current = calculateVolatility(
    returns.slice(-windowSize)
  );
  const annualized = annualizeVolatility(current);
  
  // Calculate rolling volatility for percentile and trend
  const rollingVol = calculateRollingVolatility(returns, windowSize);
  
  let percentile = 50;
  let trend: 'increasing' | 'decreasing' | 'stable' = 'stable';
  
  if (rollingVol.length > 0) {
    const sorted = [...rollingVol].sort((a, b) => a - b);
    const currentVol = rollingVol[rollingVol.length - 1];
    const rank = sorted.findIndex((v) => v >= currentVol);
    percentile = (rank / sorted.length) * 100;
    
    // Determine trend by comparing recent vs. earlier volatility
    if (rollingVol.length >= 10) {
      const recentAvg = rollingVol.slice(-5).reduce((sum, v) => sum + v, 0) / 5;
      const earlierAvg = rollingVol.slice(-10, -5).reduce((sum, v) => sum + v, 0) / 5;
      
      if (recentAvg > earlierAvg * 1.1) {
        trend = 'increasing';
      } else if (recentAvg < earlierAvg * 0.9) {
        trend = 'decreasing';
      }
    }
  }

  return {
    current,
    annualized,
    percentile,
    trend,
  };
}

/**
 * Calculate beta (systematic risk) relative to a benchmark
 * 
 * @param assetReturns - Returns of the asset
 * @param benchmarkReturns - Returns of the benchmark
 * @returns Beta result with correlation and R²
 */
export function calculateBeta(
  assetReturns: number[],
  benchmarkReturns: number[]
): BetaResult {
  if (
    assetReturns.length !== benchmarkReturns.length ||
    assetReturns.length === 0
  ) {
    return { beta: 0, correlation: 0, rSquared: 0 };
  }

  // Filter valid pairs
  const validPairs: Array<[number, number]> = [];
  for (let i = 0; i < assetReturns.length; i++) {
    if (
      !isNaN(assetReturns[i]) &&
      isFinite(assetReturns[i]) &&
      !isNaN(benchmarkReturns[i]) &&
      isFinite(benchmarkReturns[i])
    ) {
      validPairs.push([assetReturns[i], benchmarkReturns[i]]);
    }
  }

  if (validPairs.length === 0) {
    return { beta: 0, correlation: 0, rSquared: 0 };
  }

  const n = validPairs.length;
  const assetMean =
    validPairs.reduce((sum, [a, _]) => sum + a, 0) / n;
  const benchmarkMean =
    validPairs.reduce((sum, [_, b]) => sum + b, 0) / n;

  // Calculate covariance and variances
  let covariance = 0;
  let assetVariance = 0;
  let benchmarkVariance = 0;

  for (const [asset, benchmark] of validPairs) {
    const assetDev = asset - assetMean;
    const benchmarkDev = benchmark - benchmarkMean;

    covariance += assetDev * benchmarkDev;
    assetVariance += assetDev * assetDev;
    benchmarkVariance += benchmarkDev * benchmarkDev;
  }

  covariance /= n;
  assetVariance /= n;
  benchmarkVariance /= n;

  // Calculate beta
  const beta = benchmarkVariance !== 0 ? covariance / benchmarkVariance : 0;

  // Calculate correlation
  const correlation =
    assetVariance !== 0 && benchmarkVariance !== 0
      ? covariance / Math.sqrt(assetVariance * benchmarkVariance)
      : 0;

  // Calculate R²
  const rSquared = correlation * correlation;

  return { beta, correlation, rSquared };
}

/**
 * Calculate realized volatility from prices
 * 
 * @param prices - Array of prices
 * @param windowSize - Window size for calculation
 * @returns Realized volatility
 */
export function calculateRealizedVolatility(
  prices: number[],
  windowSize: number = 20
): number {
  if (prices.length < 2) {
    return 0;
  }

  // Calculate returns using shared utility
  const returns = calculateReturns(prices);

  // Use last windowSize returns
  const recentReturns = returns.slice(-windowSize);
  return calculateVolatility(recentReturns);
}
