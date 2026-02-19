'use client';

import { useState } from 'react';
import { mockPositions, Position } from '@/mock/positions';
import { PositionsTable } from '@/components/PositionsTable';
import { formatCurrency, formatDateTime } from '@/lib/utils/format';
import { 
  Filter,
  Download,
  X,
  TrendingUp,
  AlertCircle,
  Calendar,
  ExternalLink,
  DollarSign
} from 'lucide-react';

export default function PositionsPage() {
  const [filterType, setFilterType] = useState<Position['type'] | 'all'>('all');
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);

  const filteredPositions = filterType === 'all' 
    ? mockPositions 
    : mockPositions.filter(pos => pos.type === filterType);

  const totalValue = filteredPositions.reduce((sum, pos) => sum + pos.currentValue, 0);
  const totalPnL = filteredPositions.reduce((sum, pos) => sum + pos.pnl, 0);
  const avgHealth = filteredPositions.reduce((sum, pos) => sum + pos.health, 0) / filteredPositions.length;

  const getHealthColor = (health: number) => {
    if (health >= 90) return 'text-emerald-400';
    if (health >= 70) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getHealthBg = (health: number) => {
    if (health >= 90) return 'bg-emerald-900/20 border-emerald-700/30';
    if (health >= 70) return 'bg-yellow-900/20 border-yellow-700/30';
    return 'bg-red-900/20 border-red-700/30';
  };

  const handleExport = () => {
    const timestamp = new Date().toISOString().split('T')[0];
    const csv = [
      ['ID', 'Type', 'Protocol', 'Tokens', 'Deposited', 'Current Value', 'APY', 'PnL', 'PnL %', 'Health', 'Status'].join(','),
      ...filteredPositions.map(pos => [
        pos.id,
        pos.type,
        pos.protocol,
        pos.tokens.join('/'),
        pos.depositedAmount,
        pos.currentValue,
        pos.apy,
        pos.pnl,
        pos.pnlPercentage,
        pos.health,
        pos.status
      ].join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `positions-${timestamp}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Positions</h1>
          <p className="text-slate-400">Detailed view of all your active DeFi positions</p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <p className="text-slate-400 text-sm font-medium mb-2">Active Positions</p>
            <p className="text-3xl font-bold text-white">{filteredPositions.length}</p>
          </div>
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <p className="text-slate-400 text-sm font-medium mb-2">Total Value</p>
            <p className="text-3xl font-bold text-white">
              ${formatCurrency(totalValue)}
            </p>
          </div>
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <p className="text-slate-400 text-sm font-medium mb-2">Total P&L</p>
            <p className={`text-3xl font-bold ${totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {totalPnL >= 0 ? '+' : ''}${formatCurrency(totalPnL)}
            </p>
          </div>
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <p className="text-slate-400 text-sm font-medium mb-2">Avg Health</p>
            <p className={`text-3xl font-bold ${getHealthColor(avgHealth)}`}>
              {avgHealth.toFixed(0)}
            </p>
          </div>
        </div>

        {/* Filters and Actions */}
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="flex items-center gap-2 flex-wrap">
            <Filter className="h-5 w-5 text-slate-400" />
            <button
              onClick={() => setFilterType('all')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                filterType === 'all'
                  ? 'bg-emerald-600 text-white shadow-lg'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              All Positions
            </button>
            <button
              onClick={() => setFilterType('Earn')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                filterType === 'Earn'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              Earn
            </button>
            <button
              onClick={() => setFilterType('LP')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                filterType === 'LP'
                  ? 'bg-purple-600 text-white shadow-lg'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              LP
            </button>
            <button
              onClick={() => setFilterType('Farm')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                filterType === 'Farm'
                  ? 'bg-amber-600 text-white shadow-lg'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              Farm
            </button>
          </div>
          <div className="md:ml-auto">
            <button
              onClick={handleExport}
              className="w-full md:w-auto px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-lg border border-slate-700 transition-all flex items-center justify-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Positions Table */}
        <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl overflow-hidden">
          <PositionsTable 
            positions={filteredPositions}
            onPositionClick={setSelectedPosition}
          />
        </div>
      </div>

      {/* Position Detail Modal */}
      {selectedPosition && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-2xl bg-slate-900 rounded-xl shadow-2xl border border-slate-700 max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-slate-900 border-b border-slate-700 p-6 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h2 className="text-2xl font-bold text-white">{selectedPosition.protocol}</h2>
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-full border ${
                    selectedPosition.type === 'Earn' ? 'bg-blue-900/20 text-blue-400 border-blue-700/30' :
                    selectedPosition.type === 'LP' ? 'bg-purple-900/20 text-purple-400 border-purple-700/30' :
                    'bg-amber-900/20 text-amber-400 border-amber-700/30'
                  }`}>
                    {selectedPosition.type}
                  </span>
                </div>
                <p className="text-slate-400 text-sm">
                  {selectedPosition.tokens.join(' / ')}
                </p>
              </div>
              <button
                onClick={() => setSelectedPosition(null)}
                className="text-slate-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Key Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <DollarSign className="h-4 w-4 text-slate-400" />
                    <span className="text-xs text-slate-400 font-medium">Current Value</span>
                  </div>
                  <p className="text-2xl font-bold text-white">
                    ${formatCurrency(selectedPosition.currentValue)}
                  </p>
                </div>
                <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                    <span className="text-xs text-slate-400 font-medium">APY</span>
                  </div>
                  <p className="text-2xl font-bold text-emerald-400">
                    {selectedPosition.apy.toFixed(2)}%
                  </p>
                </div>
                <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className={`h-4 w-4 ${selectedPosition.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`} />
                    <span className="text-xs text-slate-400 font-medium">P&L</span>
                  </div>
                  <p className={`text-2xl font-bold ${selectedPosition.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {selectedPosition.pnl >= 0 ? '+' : ''}${formatCurrency(selectedPosition.pnl)}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {selectedPosition.pnlPercentage >= 0 ? '+' : ''}{selectedPosition.pnlPercentage.toFixed(2)}%
                  </p>
                </div>
                <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className={`h-4 w-4 ${getHealthColor(selectedPosition.health)}`} />
                    <span className="text-xs text-slate-400 font-medium">Health Score</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <p className={`text-2xl font-bold ${getHealthColor(selectedPosition.health)}`}>
                      {selectedPosition.health}
                    </p>
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${getHealthBg(selectedPosition.health)}`}>
                      {selectedPosition.health >= 90 ? 'Healthy' : selectedPosition.health >= 70 ? 'Fair' : 'At Risk'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Position Details */}
              <div className="space-y-3">
                <h3 className="text-lg font-bold text-white">Position Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Position ID</span>
                    <span className="text-white font-mono">{selectedPosition.id}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Deposited Amount</span>
                    <span className="text-white font-medium">
                      ${formatCurrency(selectedPosition.depositedAmount)}
                    </span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Entry Date</span>
                    <span className="text-white flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />
                      {formatDateTime(selectedPosition.entryDate)}
                    </span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Last Update</span>
                    <span className="text-white">{formatDateTime(selectedPosition.lastUpdate)}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Status</span>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      selectedPosition.status === 'active' ? 'bg-emerald-900/20 text-emerald-400 border border-emerald-700/30' :
                      selectedPosition.status === 'closed' ? 'bg-slate-700 text-slate-300 border border-slate-600' :
                      'bg-yellow-900/20 text-yellow-400 border border-yellow-700/30'
                    }`}>
                      {selectedPosition.status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Metadata */}
              {selectedPosition.metadata && (
                <div className="space-y-3">
                  <h3 className="text-lg font-bold text-white">Technical Details</h3>
                  <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                    <div className="space-y-2 text-sm font-mono">
                      {selectedPosition.metadata.vaultId && (
                        <div className="flex justify-between">
                          <span className="text-slate-400">Vault ID:</span>
                          <span className="text-white">{selectedPosition.metadata.vaultId}</span>
                        </div>
                      )}
                      {selectedPosition.metadata.poolAddress && (
                        <div className="flex justify-between">
                          <span className="text-slate-400">Pool:</span>
                          <a
                            href={`https://bscscan.com/address/${selectedPosition.metadata.poolAddress}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-emerald-400 hover:text-emerald-300 transition-colors flex items-center gap-1"
                          >
                            {selectedPosition.metadata.poolAddress.slice(0, 6)}...{selectedPosition.metadata.poolAddress.slice(-4)}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        </div>
                      )}
                      {selectedPosition.metadata.farmId && (
                        <div className="flex justify-between">
                          <span className="text-slate-400">Farm ID:</span>
                          <span className="text-white">{selectedPosition.metadata.farmId}</span>
                        </div>
                      )}
                      {selectedPosition.metadata.lpTokenBalance && (
                        <div className="flex justify-between">
                          <span className="text-slate-400">LP Balance:</span>
                          <span className="text-white">{selectedPosition.metadata.lpTokenBalance}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-4">
                <button className="flex-1 px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-lg border border-slate-700 transition-all">
                  Increase Position
                </button>
                <button className="flex-1 px-4 py-3 bg-red-900/20 hover:bg-red-900/30 text-red-400 font-medium rounded-lg border border-red-700/30 transition-all">
                  Close Position
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
