'use client';

import { useState } from 'react';
import Link from 'next/link';
import { mockPortfolio } from '@/mock/portfolio';
import { TxModal } from '@/components/TxModal';
import { formatCurrency, formatDate, formatTxHash } from '@/lib/utils/format';
import { 
  TrendingUp, 
  Wallet, 
  Coins, 
  DollarSign, 
  ArrowDownCircle, 
  ArrowUpCircle,
  Activity,
  ExternalLink,
  Calendar
} from 'lucide-react';

export default function DashboardPage() {
  const [txModalOpen, setTxModalOpen] = useState(false);
  const [txModalType, setTxModalType] = useState<'deposit' | 'withdraw'>('deposit');

  const handleOpenTxModal = (type: 'deposit' | 'withdraw') => {
    setTxModalType(type);
    setTxModalOpen(true);
  };

  const isPositivePnL = mockPortfolio.pnlPercentage >= 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Portfolio Dashboard</h1>
          <p className="text-slate-400">Track your yield farming positions and performance</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Value */}
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-slate-400 text-sm font-medium">Total Value</span>
              <div className="p-2 bg-emerald-900/20 rounded-lg">
                <Wallet className="h-5 w-5 text-emerald-400" />
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-3xl font-bold text-white">
                ${formatCurrency(mockPortfolio.totalValue)}
              </p>
              <p className="text-xs text-slate-500">
                {mockPortfolio.totalShares.toLocaleString()} shares
              </p>
            </div>
          </div>

          {/* Total Deposits */}
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-slate-400 text-sm font-medium">Total Deposits</span>
              <div className="p-2 bg-blue-900/20 rounded-lg">
                <DollarSign className="h-5 w-5 text-blue-400" />
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-3xl font-bold text-white">
                ${formatCurrency(mockPortfolio.totalDeposits)}
              </p>
              <p className="text-xs text-slate-500">
                Across {mockPortfolio.positions.length} positions
              </p>
            </div>
          </div>

          {/* Yield Earned */}
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-slate-400 text-sm font-medium">Yield Earned</span>
              <div className="p-2 bg-emerald-900/20 rounded-lg">
                <Coins className="h-5 w-5 text-emerald-400" />
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-3xl font-bold text-emerald-400">
                ${formatCurrency(mockPortfolio.totalYieldEarned)}
              </p>
              <p className="text-xs text-emerald-500/70">
                All-time earnings
              </p>
            </div>
          </div>

          {/* Total PnL */}
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-slate-400 text-sm font-medium">Total P&L</span>
              <div className={`p-2 rounded-lg ${isPositivePnL ? 'bg-emerald-900/20' : 'bg-red-900/20'}`}>
                <TrendingUp className={`h-5 w-5 ${isPositivePnL ? 'text-emerald-400' : 'text-red-400'}`} />
              </div>
            </div>
            <div className="space-y-1">
              <p className={`text-3xl font-bold ${isPositivePnL ? 'text-emerald-400' : 'text-red-400'}`}>
                {isPositivePnL ? '+' : ''}${formatCurrency(mockPortfolio.totalPnL)}
              </p>
              <p className={`text-xs ${isPositivePnL ? 'text-emerald-500/70' : 'text-red-500/70'}`}>
                {isPositivePnL ? '+' : ''}{mockPortfolio.pnlPercentage.toFixed(2)}%
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={() => handleOpenTxModal('deposit')}
            className="flex-1 md:flex-none px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg shadow-lg hover:shadow-emerald-600/50 transition-all duration-200 flex items-center justify-center gap-2"
          >
            <ArrowDownCircle className="h-5 w-5" />
            Deposit
          </button>
          <button
            onClick={() => handleOpenTxModal('withdraw')}
            className="flex-1 md:flex-none px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg shadow-lg transition-all duration-200 flex items-center justify-center gap-2"
          >
            <ArrowUpCircle className="h-5 w-5" />
            Withdraw
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Active Positions */}
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Activity className="h-5 w-5 text-emerald-400" />
                Active Positions
              </h2>
              <Link href="/positions" className="text-sm text-emerald-400 hover:text-emerald-300 transition-colors flex items-center gap-1">
                View All
                <ExternalLink className="h-4 w-4" />
              </Link>
            </div>
            <div className="space-y-3">
              {mockPortfolio.positions.map((position) => {
                const positionPnL = position.currentValue - position.depositedAmount;
                const positionPnLPercent = (positionPnL / position.depositedAmount) * 100;
                const isPositive = positionPnL >= 0;

                return (
                  <div
                    key={position.id}
                    className="p-4 bg-slate-900/50 border border-slate-700 rounded-lg hover:border-emerald-700/50 transition-all cursor-pointer"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-medium text-white">{position.protocol}</h3>
                        <p className="text-sm text-slate-400">
                          {position.tokens.join(' / ')}
                        </p>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        position.type === 'Earn' ? 'bg-blue-900/20 text-blue-400 border border-blue-700/30' :
                        position.type === 'LP' ? 'bg-purple-900/20 text-purple-400 border border-purple-700/30' :
                        'bg-amber-900/20 text-amber-400 border border-amber-700/30'
                      }`}>
                        {position.type}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-slate-400 mb-1">Value</p>
                        <p className="text-white font-medium">
                          ${formatCurrency(position.currentValue)}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400 mb-1">APY</p>
                        <p className="text-emerald-400 font-medium">{position.apy}%</p>
                      </div>
                      <div>
                        <p className="text-slate-400 mb-1">Yield Earned</p>
                        <p className="text-emerald-400 font-medium">
                          +${formatCurrency(position.yieldEarned)}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400 mb-1">P&L</p>
                        <p className={`font-medium ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                          {isPositive ? '+' : ''}${formatCurrency(positionPnL)}
                          <span className="text-xs ml-1">
                            ({isPositive ? '+' : ''}{positionPnLPercent.toFixed(2)}%)
                          </span>
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-6">
              <Calendar className="h-5 w-5 text-emerald-400" />
              Recent Deposits
            </h2>
            <div className="space-y-3">
              {mockPortfolio.depositHistory.map((deposit, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-slate-900/50 border border-slate-700 rounded-lg hover:border-emerald-700/50 transition-all"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white font-medium">
                      ${formatCurrency(deposit.amount)}
                    </span>
                    <span className="text-xs text-slate-400">
                      {formatDate(deposit.timestamp)}
                    </span>
                  </div>
                  <a
                    href={`https://bscscan.com/tx/${deposit.txHash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors flex items-center gap-1"
                  >
                    {formatTxHash(deposit.txHash)}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Transaction Modal */}
      <TxModal
        isOpen={txModalOpen}
        onClose={() => setTxModalOpen(false)}
        type={txModalType}
      />
    </div>
  );
}
