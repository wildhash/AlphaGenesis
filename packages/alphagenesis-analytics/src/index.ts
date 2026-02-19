/**
 * AlphaGenesis Analytics
 * TypeScript adapter for AlphaGenesis Python analytics modules
 * 
 * This package provides TypeScript/JavaScript implementations of core
 * analytics concepts from the AlphaGenesis trading system for use in
 * web UIs and frontend applications.
 * 
 * Note: These are simplified versions for visualization and monitoring.
 * Production trading should use the full Python implementations.
 */

// Risk Analytics
export {
  calculateVaR,
  calculateParametricVaR,
  calculateCVaR,
  calculateMaxDrawdown,
  calculateSharpeRatio,
  calculateAllRiskMetrics,
  type RiskMetrics,
  type VaRResult,
  type DrawdownMetrics,
} from './risk-analytics';

// Volatility Analysis
export {
  calculateVolatility,
  calculateRollingVolatility,
  annualizeVolatility,
  calculateVolatilityMetrics,
  calculateBeta,
  calculateRealizedVolatility,
  type VolatilityMetrics,
  type BetaResult,
} from './volatility';

// Regime Detection
export {
  detectRegime,
  isTradeable,
  getRegimeLabel,
  type MarketRegime,
  type RegimeDetectionResult,
  type RegimeThresholds,
} from './regime-detection';

// Common Types
export {
  type PriceData,
  type TimeSeries,
  type Returns,
  type RiskLevel,
  RISK_LEVEL_THRESHOLDS,
} from './types';
