'use client';

import { formatCurrency } from '@/lib/utils/format';
import { 
  Shield, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle,
  Activity,
  Target
} from 'lucide-react';

export interface RiskPanelProps {
  sharpeRatio: number;
  volatility: number;
  maxDrawdown: number;
  var95?: number;
  beta?: number;
  showAll?: boolean;
  className?: string;
}

export function RiskPanel({
  sharpeRatio,
  volatility,
  maxDrawdown,
  var95,
  beta,
  showAll = true,
  className = '',
}: RiskPanelProps) {
  const getRiskLevel = (sharpeRatio: number): 'low' | 'medium' | 'high' => {
    if (sharpeRatio >= 2.0) return 'low';
    if (sharpeRatio >= 1.0) return 'medium';
    return 'high';
  };

  const getVolatilityLevel = (vol: number): 'low' | 'medium' | 'high' => {
    if (vol <= 10) return 'low';
    if (vol <= 20) return 'medium';
    return 'high';
  };

  const getRiskColor = (level: 'low' | 'medium' | 'high') => {
    switch (level) {
      case 'low':
        return 'text-emerald-400 bg-emerald-900/20 border-emerald-700/30';
      case 'medium':
        return 'text-yellow-400 bg-yellow-900/20 border-yellow-700/30';
      case 'high':
        return 'text-red-400 bg-red-900/20 border-red-700/30';
    }
  };

  const riskLevel = getRiskLevel(sharpeRatio);
  const volLevel = getVolatilityLevel(volatility);

  return (
    <div className={`bg-slate-900 rounded-xl border border-slate-800 ${className}`}>
      <div className="px-6 py-4 border-b border-slate-800">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Shield className="h-5 w-5 text-emerald-400" />
          Risk Metrics
        </h3>
        <p className="text-sm text-slate-400 mt-1">
          Portfolio risk analysis and indicators
        </p>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Sharpe Ratio */}
          <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Sharpe Ratio</span>
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white mb-2">
              {sharpeRatio.toFixed(2)}
            </div>
            <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getRiskColor(riskLevel)}`}>
              {riskLevel.toUpperCase()} RISK
            </span>
          </div>

          {/* Volatility */}
          <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Volatility (Annual)</span>
              <Activity className="h-4 w-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white mb-2">
              {volatility.toFixed(2)}%
            </div>
            <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getRiskColor(volLevel)}`}>
              {volLevel.toUpperCase()}
            </span>
          </div>

          {/* Max Drawdown */}
          <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Max Drawdown</span>
              <TrendingDown className="h-4 w-4 text-red-400" />
            </div>
            <div className="text-2xl font-bold text-red-400 mb-2">
              -{maxDrawdown.toFixed(2)}%
            </div>
            <span className="text-xs text-slate-500">
              Historical peak decline
            </span>
          </div>

          {/* VaR (if provided) */}
          {showAll && var95 !== undefined && (
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">VaR (95%)</span>
                <AlertTriangle className="h-4 w-4 text-yellow-400" />
              </div>
              <div className="text-2xl font-bold text-white mb-2">
                ${formatCurrency(var95)}
              </div>
              <span className="text-xs text-slate-500">
                Daily at 95% confidence
              </span>
            </div>
          )}

          {/* Beta (if provided) */}
          {showAll && beta !== undefined && (
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">Beta</span>
                <Target className="h-4 w-4 text-purple-400" />
              </div>
              <div className="text-2xl font-bold text-white mb-2">
                {beta.toFixed(2)}
              </div>
              <span className="text-xs text-slate-500">
                Market correlation
              </span>
            </div>
          )}
        </div>

        {/* Risk Level Explanation */}
        <div className="mt-6 p-4 bg-slate-800/30 rounded-lg border border-slate-700">
          <div className="flex items-start gap-3">
            <Shield className={`h-5 w-5 flex-shrink-0 mt-0.5 ${
              riskLevel === 'low' ? 'text-emerald-400' :
              riskLevel === 'medium' ? 'text-yellow-400' :
              'text-red-400'
            }`} />
            <div className="flex-1">
              <div className="font-medium text-white mb-1">
                {riskLevel === 'low' && 'Low Risk Profile'}
                {riskLevel === 'medium' && 'Medium Risk Profile'}
                {riskLevel === 'high' && 'High Risk Profile'}
              </div>
              <p className="text-sm text-slate-400">
                {riskLevel === 'low' && 'Strong risk-adjusted returns with Sharpe ratio above 2.0. Excellent performance relative to risk taken.'}
                {riskLevel === 'medium' && 'Moderate risk-adjusted returns with Sharpe ratio between 1.0-2.0. Acceptable risk/reward balance.'}
                {riskLevel === 'high' && 'Lower risk-adjusted returns with Sharpe ratio below 1.0. Consider reviewing position sizes.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
