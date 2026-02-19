# AlphaGenesis Analytics

TypeScript adapter for AlphaGenesis Python analytics modules. This package provides frontend-friendly implementations of core risk and market analysis concepts for use in web UIs and monitoring dashboards.

## Overview

This package is **adapted from** the AlphaGenesis Python codebase and provides TypeScript implementations of:

- **Risk Analytics** - VaR, CVaR, drawdown calculations (from `alphagenesis/risk/var_calculator.py`)
- **Volatility Analysis** - Historical volatility, beta calculations (from `alphagenesis/risk/garch_model.py`)
- **Regime Detection** - Market regime classification (from `alphagenesis/features/market_regime.py`)

## Attribution

This package adapts concepts and algorithms from:
- `alphagenesis/risk/var_calculator.py` - VaR and risk metrics
- `alphagenesis/risk/garch_model.py` - Volatility analysis
- `alphagenesis/features/market_regime.py` - Market regime detection

## Important Notes

⚠️ **This is a simplified version for UI/visualization purposes.**

For production trading, use the full Python implementations which include:
- Advanced GARCH models for volatility forecasting
- Hidden Markov Models for regime detection
- Monte Carlo simulations
- Portfolio-level risk analysis

## Installation

```bash
# If using in a monorepo
npm install @alphagenesis/analytics

# Or import directly (TypeScript source)
```

## Usage Examples

### Risk Analytics

```typescript
import { calculateVaR, calculateCVaR, calculateMaxDrawdown } from '@alphagenesis/analytics';

// Calculate Value at Risk
const returns = [-0.02, 0.01, -0.015, 0.03, -0.01];
const var95 = calculateVaR(returns, 0.95);
console.log(`VaR (95%): ${var95}`);

// Calculate Conditional VaR (Expected Shortfall)
const cvar95 = calculateCVaR(returns, 0.95);
console.log(`CVaR (95%): ${cvar95}`);

// Calculate maximum drawdown
const equityCurve = [10000, 10500, 10200, 11000, 10800, 11500];
const drawdown = calculateMaxDrawdown(equityCurve);
console.log(`Max Drawdown: ${drawdown.maxDrawdownPercent}%`);
```

### Volatility Analysis

```typescript
import { calculateVolatility, calculateVolatilityMetrics, calculateBeta } from '@alphagenesis/analytics';

// Calculate historical volatility
const returns = [-0.02, 0.01, -0.015, 0.03, -0.01];
const vol = calculateVolatility(returns);
console.log(`Volatility: ${vol}`);

// Get volatility metrics with percentile and trend
const metrics = calculateVolatilityMetrics(returns, 20);
console.log(`Volatility percentile: ${metrics.percentile}`);
console.log(`Trend: ${metrics.trend}`);

// Calculate beta vs benchmark
const assetReturns = [0.01, -0.02, 0.015, -0.01];
const benchmarkReturns = [0.005, -0.015, 0.01, -0.005];
const beta = calculateBeta(assetReturns, benchmarkReturns);
console.log(`Beta: ${beta.beta}`);
```

### Regime Detection

```typescript
import { detectRegime, isTradeable } from '@alphagenesis/analytics';

// Detect market regime
const prices = [100, 102, 101, 103, 105, 104, 107, 110, 108, 112];
const regime = detectRegime(prices);

console.log(`Regime: ${regime.regime}`);
console.log(`Confidence: ${regime.confidence}`);
console.log(`Trend strength: ${regime.trendStrength}`);
console.log(`Factors: ${regime.factors.join(', ')}`);

// Check if tradeable
if (isTradeable(regime)) {
  console.log('Market conditions suitable for trading');
}
```

### Complete Risk Metrics

```typescript
import { calculateAllRiskMetrics } from '@alphagenesis/analytics';

const returns = [...]; // Your returns data
const equityCurve = [...]; // Your equity curve

const metrics = calculateAllRiskMetrics(returns, equityCurve);
console.log(metrics);
// {
//   var95: 0.023,
//   var99: 0.034,
//   cvar95: 0.028,
//   cvar99: 0.041,
//   maxDrawdown: 15.2,
//   sharpeRatio: 1.8
// }
```

## API Reference

### Risk Analytics

- `calculateVaR(returns, confidenceLevel)` - Historical Value at Risk
- `calculateParametricVaR(returns, confidenceLevel)` - Parametric VaR (normal distribution)
- `calculateCVaR(returns, confidenceLevel)` - Conditional VaR / Expected Shortfall
- `calculateMaxDrawdown(equityCurve)` - Maximum drawdown metrics
- `calculateSharpeRatio(returns, riskFreeRate, periodsPerYear)` - Sharpe ratio
- `calculateAllRiskMetrics(returns, equityCurve)` - All risk metrics at once

### Volatility Analysis

- `calculateVolatility(returns)` - Historical volatility (std dev)
- `calculateRollingVolatility(returns, windowSize)` - Rolling window volatility
- `annualizeVolatility(volatility, periodsPerYear)` - Annualize period volatility
- `calculateVolatilityMetrics(returns, windowSize)` - Comprehensive volatility metrics
- `calculateBeta(assetReturns, benchmarkReturns)` - Beta, correlation, R²
- `calculateRealizedVolatility(prices, windowSize)` - Realized volatility from prices

### Regime Detection

- `detectRegime(prices, volume?, thresholds?)` - Detect market regime
- `isTradeable(result)` - Check if regime is suitable for trading
- `getRegimeLabel(regime)` - Get human-readable regime label

## Types

All TypeScript interfaces and types are available:

```typescript
import type {
  RiskMetrics,
  VaRResult,
  DrawdownMetrics,
  VolatilityMetrics,
  BetaResult,
  MarketRegime,
  RegimeDetectionResult,
  PriceData,
  TimeSeries,
} from '@alphagenesis/analytics';
```

## What's NOT Included

This package focuses on what UIs actually need and excludes:

- Complex GARCH models (use Python for forecasting)
- Monte Carlo simulations (computationally intensive)
- Hidden Markov Models (use Python for advanced regime detection)
- Portfolio optimization (use Python)
- Full backtesting engine (use Python)

## Contributing

This package should stay simple and focused on UI needs. Complex analytics belong in the Python codebase.

## License

MIT - Same as AlphaGenesis core
