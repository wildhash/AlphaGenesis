export interface RiskMetrics {
  var: {
    daily: number;
    weekly: number;
    monthly: number;
  };
  cvar: {
    daily: number;
    weekly: number;
    monthly: number;
  };
  maxDrawdown: {
    value: number;
    percentage: number;
    startDate: number;
    endDate: number;
  };
  volatility: {
    daily: number;
    weekly: number;
    monthly: number;
    annualized: number;
  };
  sharpeRatio: number;
  sortinoRatio: number;
  beta: number;
  exposures: {
    protocol: string;
    percentage: number;
    value: number;
  }[];
  marketRegime: {
    current: 'trending' | 'volatile' | 'calm';
    confidence: number;
    lastUpdate: number;
  };
  concentrationRisk: {
    herfindahlIndex: number;
    maxSingleExposure: number;
  };
  liquidityRisk: {
    score: number; // 0-100
    avgDailyVolume: number;
    estimatedSlippage: number;
  };
}

export const mockRiskMetrics: RiskMetrics = {
  var: {
    daily: 1250.50, // $1,250.50 max loss at 95% confidence
    weekly: 3875.25, // $3,875.25 max loss at 95% confidence
    monthly: 8920.75, // $8,920.75 max loss at 95% confidence
  },
  cvar: {
    daily: 1875.75, // Conditional VaR (expected loss beyond VaR)
    weekly: 5812.60,
    monthly: 13380.50,
  },
  maxDrawdown: {
    value: 6450.00, // $6,450 max historical drawdown
    percentage: 5.2, // 5.2% from peak
    startDate: Date.now() - 45 * 24 * 60 * 60 * 1000,
    endDate: Date.now() - 38 * 24 * 60 * 60 * 1000,
  },
  volatility: {
    daily: 0.85, // 0.85% daily volatility
    weekly: 2.15, // 2.15% weekly volatility
    monthly: 4.50, // 4.50% monthly volatility
    annualized: 13.50, // 13.50% annualized volatility
  },
  sharpeRatio: 1.85, // Risk-adjusted return measure
  sortinoRatio: 2.45, // Downside risk-adjusted return
  beta: 0.72, // Market correlation (0.72 = 72% correlated with market)
  exposures: [
    {
      protocol: 'AsterEarn',
      percentage: 45.5,
      value: 65000.00,
    },
    {
      protocol: 'PancakeSwap',
      percentage: 38.2,
      value: 54550.00,
    },
    {
      protocol: 'Alpaca Finance',
      percentage: 10.8,
      value: 15400.00,
    },
    {
      protocol: 'Venus Protocol',
      percentage: 5.5,
      value: 7850.00,
    },
  ],
  marketRegime: {
    current: 'calm', // Current market regime
    confidence: 0.82, // 82% confidence in classification
    lastUpdate: Date.now() - 5 * 60 * 1000, // Updated 5 minutes ago
  },
  concentrationRisk: {
    herfindahlIndex: 0.32, // Lower is more diversified (0-1 scale)
    maxSingleExposure: 45.5, // 45.5% in single protocol
  },
  liquidityRisk: {
    score: 78, // 78/100 liquidity score (higher is better)
    avgDailyVolume: 2450000.00, // $2.45M average daily volume
    estimatedSlippage: 0.35, // 0.35% estimated slippage for full exit
  },
};

// Historical risk data for charts
export interface HistoricalRiskData {
  timestamp: number;
  var: number;
  volatility: number;
  sharpeRatio: number;
  regime: 'trending' | 'volatile' | 'calm';
}

export const mockHistoricalRisk: HistoricalRiskData[] = [
  {
    timestamp: Date.now() - 60 * 24 * 60 * 60 * 1000,
    var: 1150.00,
    volatility: 0.78,
    sharpeRatio: 1.65,
    regime: 'calm',
  },
  {
    timestamp: Date.now() - 45 * 24 * 60 * 60 * 1000,
    var: 1680.00,
    volatility: 1.25,
    sharpeRatio: 1.42,
    regime: 'volatile',
  },
  {
    timestamp: Date.now() - 30 * 24 * 60 * 60 * 1000,
    var: 1420.00,
    volatility: 0.95,
    sharpeRatio: 1.58,
    regime: 'trending',
  },
  {
    timestamp: Date.now() - 15 * 24 * 60 * 60 * 1000,
    var: 1310.00,
    volatility: 0.88,
    sharpeRatio: 1.72,
    regime: 'calm',
  },
  {
    timestamp: Date.now() - 7 * 24 * 60 * 60 * 1000,
    var: 1280.00,
    volatility: 0.86,
    sharpeRatio: 1.80,
    regime: 'calm',
  },
  {
    timestamp: Date.now(),
    var: 1250.50,
    volatility: 0.85,
    sharpeRatio: 1.85,
    regime: 'calm',
  },
];

// Helper functions
export const getRiskLevel = (sharpeRatio: number): 'low' | 'medium' | 'high' => {
  if (sharpeRatio >= 2.0) return 'low';
  if (sharpeRatio >= 1.0) return 'medium';
  return 'high';
};

export const getVolatilityLevel = (annualizedVol: number): 'low' | 'medium' | 'high' => {
  if (annualizedVol <= 10) return 'low';
  if (annualizedVol <= 20) return 'medium';
  return 'high';
};

export const getDiversificationScore = (herfindahlIndex: number): number => {
  // Convert Herfindahl index to a 0-100 score (lower HHI = higher diversification)
  return Math.round((1 - herfindahlIndex) * 100);
};
