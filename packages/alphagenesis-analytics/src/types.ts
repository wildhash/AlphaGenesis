/**
 * Common TypeScript types for AlphaGenesis Analytics
 * Adapted from AlphaGenesis Python modules
 */

export interface PriceData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface TimeSeries {
  timestamps: number[];
  values: number[];
}

export interface Returns {
  values: number[];
  mean: number;
  std: number;
}

export type RiskLevel = 'low' | 'medium' | 'high' | 'extreme';

export interface PercentileRange {
  min: number;
  max: number;
}

export const RISK_LEVEL_THRESHOLDS: Record<RiskLevel, PercentileRange> = {
  low: { min: 0, max: 25 },
  medium: { min: 25, max: 75 },
  high: { min: 75, max: 95 },
  extreme: { min: 95, max: 100 },
};
