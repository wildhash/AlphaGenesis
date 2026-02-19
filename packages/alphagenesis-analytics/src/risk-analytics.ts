/**
 * Risk Analytics Module
 * Adapted from AlphaGenesis risk module (alphagenesis/risk/var_calculator.py)
 * 
 * Provides TypeScript implementations of key risk metrics:
 * - Value at Risk (VaR)
 * - Conditional VaR (CVaR/Expected Shortfall)
 * - Maximum Drawdown
 * 
 * Note: This is a simplified version for UI/frontend use.
 * For production trading, use the full Python implementation.
 */

export interface RiskMetrics {
  var95: number;
  var99: number;
  cvar95: number;
  cvar99: number;
  maxDrawdown: number;
  sharpeRatio: number;
}

export interface VaRResult {
  value: number;
  confidenceLevel: number;
  method: 'historical' | 'parametric';
}

export interface DrawdownMetrics {
  maxDrawdown: number;
  maxDrawdownPercent: number;
  currentDrawdown: number;
  currentDrawdownPercent: number;
  peakValue: number;
  troughValue: number;
}

/**
 * Calculate historical Value at Risk (VaR)
 * Adapted from VaRCalculator.historical_var in var_calculator.py
 * 
 * @param returns - Array of returns
 * @param confidenceLevel - Confidence level (e.g., 0.95 for 95%)
 * @returns VaR value (positive number representing potential loss)
 */
export function calculateVaR(
  returns: number[],
  confidenceLevel: number = 0.95
): number {
  if (returns.length === 0) {
    return 0;
  }

  // Filter out NaN values
  const validReturns = returns.filter((r) => !isNaN(r) && isFinite(r));

  if (validReturns.length === 0) {
    return 0;
  }

  // Calculate the percentile (VaR is the negative of the percentile)
  const sortedReturns = [...validReturns].sort((a, b) => a - b);
  const index = Math.floor((1 - confidenceLevel) * sortedReturns.length);
  const var95 = -sortedReturns[Math.max(0, index)];

  return var95;
}

/**
 * Calculate parametric VaR assuming normal distribution
 * Adapted from VaRCalculator.parametric_var in var_calculator.py
 * 
 * @param returns - Array of returns
 * @param confidenceLevel - Confidence level
 * @returns VaR value
 */
export function calculateParametricVaR(
  returns: number[],
  confidenceLevel: number = 0.95
): number {
  if (returns.length === 0) {
    return 0;
  }

  const validReturns = returns.filter((r) => !isNaN(r) && isFinite(r));

  if (validReturns.length === 0) {
    return 0;
  }

  // Calculate mean and standard deviation
  const mean = validReturns.reduce((sum, r) => sum + r, 0) / validReturns.length;
  const variance =
    validReturns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) /
    validReturns.length;
  const std = Math.sqrt(variance);

  // Z-score for normal distribution (approximation)
  const zScore = getZScore(1 - confidenceLevel);

  // Calculate VaR
  const var95 = -(mean + zScore * std);

  return var95;
}

/**
 * Calculate Conditional VaR (CVaR/Expected Shortfall)
 * Adapted from VaRCalculator.conditional_var in var_calculator.py
 * 
 * CVaR is the expected loss given that the loss exceeds VaR.
 * 
 * @param returns - Array of returns
 * @param confidenceLevel - Confidence level
 * @returns CVaR value
 */
export function calculateCVaR(
  returns: number[],
  confidenceLevel: number = 0.95
): number {
  if (returns.length === 0) {
    return 0;
  }

  const validReturns = returns.filter((r) => !isNaN(r) && isFinite(r));

  if (validReturns.length === 0) {
    return 0;
  }

  // First calculate VaR
  const varThreshold = calculateVaR(validReturns, confidenceLevel);

  // Find all losses exceeding VaR
  const excessLosses = validReturns.filter((r) => -r > varThreshold);

  if (excessLosses.length === 0) {
    return varThreshold;
  }

  // CVaR is the mean of losses exceeding VaR
  const cvar =
    -excessLosses.reduce((sum, r) => sum + r, 0) / excessLosses.length;

  return cvar;
}

/**
 * Calculate maximum drawdown from equity curve
 * 
 * @param equityCurve - Array of portfolio values over time
 * @returns Drawdown metrics
 */
export function calculateMaxDrawdown(equityCurve: number[]): DrawdownMetrics {
  if (equityCurve.length === 0) {
    return {
      maxDrawdown: 0,
      maxDrawdownPercent: 0,
      currentDrawdown: 0,
      currentDrawdownPercent: 0,
      peakValue: 0,
      troughValue: 0,
    };
  }

  let maxDrawdown = 0;
  let maxDrawdownPercent = 0;
  let peak = equityCurve[0];
  let peakValue = equityCurve[0];
  let troughValue = equityCurve[0];

  for (let i = 1; i < equityCurve.length; i++) {
    if (equityCurve[i] > peak) {
      peak = equityCurve[i];
    }

    const drawdown = peak - equityCurve[i];
    const drawdownPercent = peak > 0 ? (drawdown / peak) * 100 : 0;

    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown;
      maxDrawdownPercent = drawdownPercent;
      peakValue = peak;
      troughValue = equityCurve[i];
    }
  }

  // Current drawdown
  const currentPeak = Math.max(...equityCurve);
  const currentValue = equityCurve[equityCurve.length - 1];
  const currentDrawdown = currentPeak - currentValue;
  const currentDrawdownPercent =
    currentPeak > 0 ? (currentDrawdown / currentPeak) * 100 : 0;

  return {
    maxDrawdown,
    maxDrawdownPercent,
    currentDrawdown,
    currentDrawdownPercent,
    peakValue,
    troughValue,
  };
}

/**
 * Calculate Sharpe Ratio
 * 
 * @param returns - Array of returns
 * @param riskFreeRate - Risk-free rate (default: 0)
 * @param periodsPerYear - Number of periods per year for annualization (default: 252 for daily)
 * @returns Annualized Sharpe Ratio
 */
export function calculateSharpeRatio(
  returns: number[],
  riskFreeRate: number = 0,
  periodsPerYear: number = 252
): number {
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
  const std = Math.sqrt(variance);

  if (std === 0) {
    return 0;
  }

  // Annualize
  const annualizedReturn = mean * periodsPerYear;
  const annualizedStd = std * Math.sqrt(periodsPerYear);

  return (annualizedReturn - riskFreeRate) / annualizedStd;
}

/**
 * Calculate all risk metrics at once
 * 
 * @param returns - Array of returns
 * @param equityCurve - Array of portfolio values
 * @returns Complete risk metrics
 */
export function calculateAllRiskMetrics(
  returns: number[],
  equityCurve: number[]
): RiskMetrics {
  const var95 = calculateVaR(returns, 0.95);
  const var99 = calculateVaR(returns, 0.99);
  const cvar95 = calculateCVaR(returns, 0.95);
  const cvar99 = calculateCVaR(returns, 0.99);
  const { maxDrawdownPercent } = calculateMaxDrawdown(equityCurve);
  const sharpeRatio = calculateSharpeRatio(returns);

  return {
    var95,
    var99,
    cvar95,
    cvar99,
    maxDrawdown: maxDrawdownPercent,
    sharpeRatio,
  };
}

/**
 * Get Z-score for normal distribution (approximation)
 * Used for parametric VaR calculation
 */
function getZScore(alpha: number): number {
  // Approximation of inverse normal CDF for common values
  // For more precision, use a proper statistical library
  const lookup: Record<string, number> = {
    '0.01': -2.326,
    '0.025': -1.96,
    '0.05': -1.645,
    '0.1': -1.282,
  };

  const key = alpha.toFixed(3);
  return lookup[key] ?? -1.645; // Default to 95% confidence
}
