'use client';

import { useState } from 'react';
import { Position } from '@/mock/positions';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, ExternalLink } from 'lucide-react';

interface PositionsTableProps {
  positions: Position[];
  onPositionClick?: (position: Position) => void;
}

export function PositionsTable({ positions, onPositionClick }: PositionsTableProps) {
  const [sortBy, setSortBy] = useState<keyof Position>('currentValue');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  const handleSort = (key: keyof Position) => {
    if (sortBy === key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(key);
      setSortDirection('desc');
    }
  };

  const sortedPositions = [...positions].sort((a, b) => {
    const aValue = a[sortBy];
    const bValue = b[sortBy];
    
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
    }
    
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortDirection === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }
    
    return 0;
  });

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

  const getTypeColor = (type: Position['type']) => {
    switch (type) {
      case 'Earn':
        return 'bg-blue-900/20 text-blue-400 border-blue-700/30';
      case 'LP':
        return 'bg-purple-900/20 text-purple-400 border-purple-700/30';
      case 'Farm':
        return 'bg-amber-900/20 text-amber-400 border-amber-700/30';
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-700">
            <th className="text-left py-4 px-4 text-sm font-medium text-slate-400">
              <button onClick={() => handleSort('protocol')} className="hover:text-emerald-400 transition-colors">
                Protocol
              </button>
            </th>
            <th className="text-left py-4 px-4 text-sm font-medium text-slate-400">
              <button onClick={() => handleSort('type')} className="hover:text-emerald-400 transition-colors">
                Type
              </button>
            </th>
            <th className="text-left py-4 px-4 text-sm font-medium text-slate-400">
              Tokens
            </th>
            <th className="text-right py-4 px-4 text-sm font-medium text-slate-400">
              <button onClick={() => handleSort('depositedAmount')} className="hover:text-emerald-400 transition-colors">
                Deposited
              </button>
            </th>
            <th className="text-right py-4 px-4 text-sm font-medium text-slate-400">
              <button onClick={() => handleSort('currentValue')} className="hover:text-emerald-400 transition-colors">
                Value
              </button>
            </th>
            <th className="text-right py-4 px-4 text-sm font-medium text-slate-400">
              <button onClick={() => handleSort('apy')} className="hover:text-emerald-400 transition-colors">
                APY
              </button>
            </th>
            <th className="text-right py-4 px-4 text-sm font-medium text-slate-400">
              <button onClick={() => handleSort('pnl')} className="hover:text-emerald-400 transition-colors">
                PnL
              </button>
            </th>
            <th className="text-center py-4 px-4 text-sm font-medium text-slate-400">
              <button onClick={() => handleSort('health')} className="hover:text-emerald-400 transition-colors">
                Health
              </button>
            </th>
            <th className="text-right py-4 px-4 text-sm font-medium text-slate-400">
              Action
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {sortedPositions.map((position) => (
            <tr
              key={position.id}
              className="hover:bg-slate-800/50 transition-colors cursor-pointer"
              onClick={() => onPositionClick?.(position)}
            >
              <td className="py-4 px-4">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-white">{position.protocol}</span>
                </div>
              </td>
              <td className="py-4 px-4">
                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${getTypeColor(position.type)}`}>
                  {position.type}
                </span>
              </td>
              <td className="py-4 px-4">
                <div className="flex items-center gap-1">
                  {position.tokens.map((token, idx) => (
                    <span key={idx} className="text-sm text-slate-300">
                      {token}
                      {idx < position.tokens.length - 1 && <span className="text-slate-600 mx-1">/</span>}
                    </span>
                  ))}
                </div>
              </td>
              <td className="py-4 px-4 text-right">
                <span className="text-white font-medium">
                  ${position.depositedAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </td>
              <td className="py-4 px-4 text-right">
                <span className="text-white font-medium">
                  ${position.currentValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </td>
              <td className="py-4 px-4 text-right">
                <span className="text-emerald-400 font-medium">
                  {position.apy.toFixed(2)}%
                </span>
              </td>
              <td className="py-4 px-4 text-right">
                <div className="flex items-center justify-end gap-1">
                  {position.pnl >= 0 ? (
                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-400" />
                  )}
                  <span className={position.pnl >= 0 ? 'text-emerald-400 font-medium' : 'text-red-400 font-medium'}>
                    ${Math.abs(position.pnl).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                  <span className={`text-xs ml-1 ${position.pnl >= 0 ? 'text-emerald-400/70' : 'text-red-400/70'}`}>
                    ({position.pnlPercentage >= 0 ? '+' : ''}{position.pnlPercentage.toFixed(2)}%)
                  </span>
                </div>
              </td>
              <td className="py-4 px-4">
                <div className="flex items-center justify-center gap-2">
                  <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${getHealthBg(position.health)}`}>
                    {position.health >= 90 ? (
                      <CheckCircle className={`h-3.5 w-3.5 ${getHealthColor(position.health)}`} />
                    ) : (
                      <AlertTriangle className={`h-3.5 w-3.5 ${getHealthColor(position.health)}`} />
                    )}
                    <span className={`text-xs font-medium ${getHealthColor(position.health)}`}>
                      {position.health}
                    </span>
                  </div>
                </div>
              </td>
              <td className="py-4 px-4 text-right">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onPositionClick?.(position);
                  }}
                  className="inline-flex items-center gap-1 text-sm text-emerald-400 hover:text-emerald-300 transition-colors"
                >
                  View
                  <ExternalLink className="h-3.5 w-3.5" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {positions.length === 0 && (
        <div className="text-center py-12">
          <p className="text-slate-400">No positions found</p>
        </div>
      )}
    </div>
  );
}
