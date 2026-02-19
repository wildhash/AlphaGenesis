'use client';

import { mockRiskMetrics, mockHistoricalRisk, getDiversificationScore } from '@/mock/risk';
import { RiskPanel } from '@/components/RiskPanel';
import { formatCurrency, formatDateTime } from '@/lib/utils/format';
import {
  Shield,
  TrendingUp,
  Activity,
  PieChart,
  AlertTriangle,
  BarChart3,
  Droplets,
  Target,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function RiskPage() {
  const diversificationScore = getDiversificationScore(mockRiskMetrics.concentrationRisk.herfindahlIndex);

  const getRegimeBadge = (regime: string) => {
    switch (regime) {
      case 'calm':
        return 'bg-emerald-900/20 text-emerald-400 border-emerald-700/30';
      case 'trending':
        return 'bg-blue-900/20 text-blue-400 border-blue-700/30';
      case 'volatile':
        return 'bg-red-900/20 text-red-400 border-red-700/30';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  const chartData = mockHistoricalRisk.map(item => ({
    date: new Date(item.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    var: item.var,
    volatility: item.volatility,
    sharpe: item.sharpeRatio,
  }));

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Risk Analytics</h1>
          <p className="text-slate-400">
            Comprehensive risk metrics and portfolio exposure analysis
          </p>
        </div>

        {/* Market Regime Indicator */}
        <div className="mb-8 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-slate-800 rounded-lg">
                <Activity className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-1">Market Regime</h3>
                <p className="text-sm text-slate-400">
                  Last updated: {formatDateTime(mockRiskMetrics.marketRegime.lastUpdate)}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm text-slate-400 mb-1">Confidence</div>
                <div className="text-xl font-bold text-white">
                  {(mockRiskMetrics.marketRegime.confidence * 100).toFixed(0)}%
                </div>
              </div>
              <span className={`px-4 py-2 text-sm font-medium rounded-full border ${getRegimeBadge(mockRiskMetrics.marketRegime.current)}`}>
                {mockRiskMetrics.marketRegime.current.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {/* Risk Panel Component */}
        <div className="mb-8">
          <RiskPanel
            sharpeRatio={mockRiskMetrics.sharpeRatio}
            volatility={mockRiskMetrics.volatility.annualized}
            maxDrawdown={mockRiskMetrics.maxDrawdown.percentage}
            var95={mockRiskMetrics.var.daily}
            beta={mockRiskMetrics.beta}
            showAll={true}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* VaR & CVaR */}
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-6">
              <AlertTriangle className="h-5 w-5 text-yellow-400" />
              Value at Risk (VaR) & CVaR
            </h3>
            <div className="space-y-4">
              {/* Daily */}
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-400">Daily (95% confidence)</span>
                  <span className="text-xs px-2 py-1 bg-slate-800 text-slate-400 rounded">1 Day</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-slate-500 mb-1">VaR</div>
                    <div className="text-xl font-bold text-white">
                      ${formatCurrency(mockRiskMetrics.var.daily)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 mb-1">CVaR</div>
                    <div className="text-xl font-bold text-red-400">
                      ${formatCurrency(mockRiskMetrics.cvar.daily)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Weekly */}
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-400">Weekly (95% confidence)</span>
                  <span className="text-xs px-2 py-1 bg-slate-800 text-slate-400 rounded">7 Days</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-slate-500 mb-1">VaR</div>
                    <div className="text-xl font-bold text-white">
                      ${formatCurrency(mockRiskMetrics.var.weekly)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 mb-1">CVaR</div>
                    <div className="text-xl font-bold text-red-400">
                      ${formatCurrency(mockRiskMetrics.cvar.weekly)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Monthly */}
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-400">Monthly (95% confidence)</span>
                  <span className="text-xs px-2 py-1 bg-slate-800 text-slate-400 rounded">30 Days</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-slate-500 mb-1">VaR</div>
                    <div className="text-xl font-bold text-white">
                      ${formatCurrency(mockRiskMetrics.var.monthly)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 mb-1">CVaR</div>
                    <div className="text-xl font-bold text-red-400">
                      ${formatCurrency(mockRiskMetrics.cvar.monthly)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Additional Risk Metrics */}
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-6">
              <BarChart3 className="h-5 w-5 text-purple-400" />
              Additional Metrics
            </h3>
            <div className="space-y-4">
              {/* Sortino Ratio */}
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-400">Sortino Ratio</span>
                  <TrendingUp className="h-4 w-4 text-emerald-400" />
                </div>
                <div className="text-2xl font-bold text-white">
                  {mockRiskMetrics.sortinoRatio.toFixed(2)}
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Downside risk-adjusted return
                </p>
              </div>

              {/* Concentration Risk */}
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-400">Diversification Score</span>
                  <PieChart className="h-4 w-4 text-blue-400" />
                </div>
                <div className="text-2xl font-bold text-white mb-2">
                  {diversificationScore}/100
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>HHI: {mockRiskMetrics.concentrationRisk.herfindahlIndex.toFixed(2)}</span>
                  <span>Max: {mockRiskMetrics.concentrationRisk.maxSingleExposure.toFixed(1)}%</span>
                </div>
              </div>

              {/* Liquidity Risk */}
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-400">Liquidity Score</span>
                  <Droplets className="h-4 w-4 text-cyan-400" />
                </div>
                <div className="text-2xl font-bold text-white mb-2">
                  {mockRiskMetrics.liquidityRisk.score}/100
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>Avg Daily Vol:</span>
                    <span>${(mockRiskMetrics.liquidityRisk.avgDailyVolume / 1000000).toFixed(2)}M</span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>Est. Slippage:</span>
                    <span>{mockRiskMetrics.liquidityRisk.estimatedSlippage.toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Protocol Exposure */}
        <div className="mb-8 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-6">
            <Target className="h-5 w-5 text-emerald-400" />
            Protocol Exposure Breakdown
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {mockRiskMetrics.exposures.map((exposure, index) => {
              const colors = [
                'from-emerald-600 to-emerald-500',
                'from-blue-600 to-blue-500',
                'from-purple-600 to-purple-500',
                'from-amber-600 to-amber-500',
              ];
              const bgColors = [
                'bg-emerald-900/20',
                'bg-blue-900/20',
                'bg-purple-900/20',
                'bg-amber-900/20',
              ];
              return (
                <div key={exposure.protocol} className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`p-2 rounded-lg ${bgColors[index % 4]}`}>
                      <Shield className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-white truncate">
                        {exposure.protocol}
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">Value</span>
                      <span className="text-sm font-bold text-white">
                        ${formatCurrency(exposure.value)}
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2">
                      <div 
                        className={`bg-gradient-to-r ${colors[index % 4]} h-2 rounded-full`}
                        style={{ width: `${exposure.percentage}%` }}
                      />
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-bold text-white">
                        {exposure.percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Historical Risk Chart */}
        <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-6">
            <Activity className="h-5 w-5 text-blue-400" />
            Historical Risk Trends
          </h3>
          
          <div className="mb-6">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis 
                  dataKey="date" 
                  stroke="#94a3b8"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#94a3b8"
                  style={{ fontSize: '12px' }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="var" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  dot={{ fill: '#10b981', r: 4 }}
                  name="VaR"
                />
                <Line 
                  type="monotone" 
                  dataKey="sharpe" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  name="Sharpe Ratio"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="text-xs text-slate-400 mb-1">Current VaR</div>
              <div className="text-lg font-bold text-emerald-400">
                ${formatCurrency(mockRiskMetrics.var.daily)}
              </div>
            </div>
            <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="text-xs text-slate-400 mb-1">Current Sharpe</div>
              <div className="text-lg font-bold text-blue-400">
                {mockRiskMetrics.sharpeRatio.toFixed(2)}
              </div>
            </div>
            <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="text-xs text-slate-400 mb-1">Volatility</div>
              <div className="text-lg font-bold text-white">
                {mockRiskMetrics.volatility.annualized.toFixed(2)}%
              </div>
            </div>
            <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="text-xs text-slate-400 mb-1">Beta</div>
              <div className="text-lg font-bold text-white">
                {mockRiskMetrics.beta.toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
