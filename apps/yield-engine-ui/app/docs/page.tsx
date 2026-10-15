'use client';

import { AuditChecklist } from '@/components/AuditChecklist';
import {
  BookOpen,
  GitBranch,
  Shield,
  Lock,
  Zap,
  TrendingUp,
  ExternalLink,
  Code,
  FileText,
  Layers,
  ArrowRight,
} from 'lucide-react';

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Documentation</h1>
          <p className="text-slate-400">
            Technical documentation and architecture overview
          </p>
        </div>

        {/* Architecture Overview */}
        <div className="mb-8 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2 mb-4">
            <Layers className="h-6 w-6 text-emerald-400" />
            Architecture Overview
          </h2>
          <p className="text-slate-300 mb-6 leading-relaxed">
            The Yield Engine is a sophisticated DeFi protocol that optimizes yield farming strategies 
            across multiple protocols while managing risk through automated hedging. The system is designed 
            to be fully non-custodial, transparent, and secure.
          </p>

          {/* Flow Diagram */}
          <div className="bg-slate-900/50 rounded-lg border border-slate-700 p-6 mb-6">
            <h3 className="text-lg font-semibold text-white mb-4">System Flow</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg">
                <div className="flex-shrink-0 w-8 h-8 bg-emerald-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                  1
                </div>
                <ArrowRight className="h-5 w-5 text-slate-500" />
                <div className="flex-1">
                  <div className="font-medium text-white">User Deposits</div>
                  <div className="text-sm text-slate-400">
                    Users deposit stablecoins and receive vault shares representing their position
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                  2
                </div>
                <ArrowRight className="h-5 w-5 text-slate-500" />
                <div className="flex-1">
                  <div className="font-medium text-white">Aster Earn Integration</div>
                  <div className="text-sm text-slate-400">
                    Funds are deposited into Aster Earn vault for base yield generation
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg">
                <div className="flex-shrink-0 w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                  3
                </div>
                <ArrowRight className="h-5 w-5 text-slate-500" />
                <div className="flex-1">
                  <div className="font-medium text-white">Stack Router Distribution</div>
                  <div className="text-sm text-slate-400">
                    Stack Router allocates capital across PancakeSwap LP positions and farms
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg">
                <div className="flex-shrink-0 w-8 h-8 bg-amber-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                  4
                </div>
                <ArrowRight className="h-5 w-5 text-slate-500" />
                <div className="flex-1">
                  <div className="font-medium text-white">Automated Hedging</div>
                  <div className="text-sm text-slate-400">
                    Delta hedging module manages impermanent loss risk through perpetual positions
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg">
                <div className="flex-shrink-0 w-8 h-8 bg-emerald-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                  5
                </div>
                <ArrowRight className="h-5 w-5 text-slate-500" />
                <div className="flex-1">
                  <div className="font-medium text-white">Yield Accrual</div>
                  <div className="text-sm text-slate-400">
                    Net yields are accumulated and reflected in increasing vault share value
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Mermaid Diagram Alternative - ASCII Style */}
          <div className="bg-slate-900 rounded-lg border border-slate-700 p-6 font-mono text-xs overflow-x-auto">
            <pre className="text-emerald-400">
{`┌─────────────────────────────────────────────────────────────────────┐
│                         YIELD ENGINE PROTOCOL                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │   User Wallet    │
                        │  (Deposits USDT) │
                        └──────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │  Vault Shares    │
                        │  (ERC-4626)      │
                        └──────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │   Aster Earn     │
                        │  (Base Yield)    │
                        └──────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │  Stack Router    │
                        │  (Allocation)    │
                        └──────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
         ┌──────────────────┐        ┌──────────────────┐
         │  PancakeSwap LP  │        │  Hedging Module  │
         │    & Farms       │        │  (Delta Neutral) │
         └──────────────────┘        └──────────────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
                        ┌──────────────────┐
                        │   Net Yield      │
                        │  → User Share    │
                        └──────────────────┘`}
            </pre>
          </div>
        </div>

        {/* Trust Model */}
        <div className="mb-8 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2 mb-6">
            <Shield className="h-6 w-6 text-emerald-400" />
            Trust Model
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-5 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-emerald-900/20 rounded-lg">
                  <Lock className="h-5 w-5 text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold text-white">Non-Custodial</h3>
              </div>
              <p className="text-sm text-slate-400 leading-relaxed">
                The protocol never takes custody of user funds. Users retain full ownership 
                of their assets through vault shares, which can be redeemed at any time.
              </p>
            </div>

            <div className="p-5 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-blue-900/20 rounded-lg">
                  <Shield className="h-5 w-5 text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold text-white">No Admin Keys</h3>
              </div>
              <p className="text-sm text-slate-400 leading-relaxed">
                Protocol operates without privileged admin access. No individual or entity 
                can modify parameters, pause operations, or access user funds.
              </p>
            </div>

            <div className="p-5 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-purple-900/20 rounded-lg">
                  <Code className="h-5 w-5 text-purple-400" />
                </div>
                <h3 className="text-lg font-semibold text-white">Immutable Parameters</h3>
              </div>
              <p className="text-sm text-slate-400 leading-relaxed">
                Core protocol parameters are set at deployment and cannot be changed. 
                This ensures predictable behavior and eliminates governance risks.
              </p>
            </div>

            <div className="p-5 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-amber-900/20 rounded-lg">
                  <GitBranch className="h-5 w-5 text-amber-400" />
                </div>
                <h3 className="text-lg font-semibold text-white">Upgrade Policy</h3>
              </div>
              <p className="text-sm text-slate-400 leading-relaxed">
                Any future upgrades will be deployed as new contracts. Users can choose 
                to migrate or continue using the existing version.
              </p>
            </div>
          </div>
        </div>

        {/* Security Checklist */}
        <div className="mb-8">
          <AuditChecklist />
        </div>

        {/* Component Documentation */}
        <div className="mb-8 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2 mb-6">
            <BookOpen className="h-6 w-6 text-emerald-400" />
            Component Documentation
          </h2>

          <div className="space-y-4">
            {/* Vault Contract */}
            <div className="p-5 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white">Vault Contract (ERC-4626)</h3>
                <Code className="h-5 w-5 text-emerald-400" />
              </div>
              <p className="text-sm text-slate-400 mb-3 leading-relaxed">
                The main entry point for users. Implements the ERC-4626 tokenized vault standard, 
                providing deposit/withdraw functionality and share accounting.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 text-xs bg-emerald-900/20 text-emerald-400 rounded border border-emerald-700/30">
                  ERC-4626
                </span>
                <span className="px-2 py-1 text-xs bg-blue-900/20 text-blue-400 rounded border border-blue-700/30">
                  Deposit/Withdraw
                </span>
                <span className="px-2 py-1 text-xs bg-purple-900/20 text-purple-400 rounded border border-purple-700/30">
                  Share Accounting
                </span>
              </div>
            </div>

            {/* Aster Earn Integration */}
            <div className="p-5 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white">Aster Earn Integration</h3>
                <Zap className="h-5 w-5 text-blue-400" />
              </div>
              <p className="text-sm text-slate-400 mb-3 leading-relaxed">
                Connects to Aster Protocol&apos;s yield-bearing vault for base layer returns. 
                Provides stable, low-risk yield on stablecoin deposits.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 text-xs bg-emerald-900/20 text-emerald-400 rounded border border-emerald-700/30">
                  Base Yield
                </span>
                <span className="px-2 py-1 text-xs bg-blue-900/20 text-blue-400 rounded border border-blue-700/30">
                  Stable Returns
                </span>
              </div>
            </div>

            {/* Stack Router */}
            <div className="p-5 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white">Stack Router</h3>
                <GitBranch className="h-5 w-5 text-purple-400" />
              </div>
              <p className="text-sm text-slate-400 mb-3 leading-relaxed">
                Intelligent capital allocation system that distributes funds across multiple 
                PancakeSwap liquidity pools and farming positions based on risk-adjusted returns.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 text-xs bg-emerald-900/20 text-emerald-400 rounded border border-emerald-700/30">
                  Auto-Allocation
                </span>
                <span className="px-2 py-1 text-xs bg-blue-900/20 text-blue-400 rounded border border-blue-700/30">
                  Multi-Protocol
                </span>
                <span className="px-2 py-1 text-xs bg-purple-900/20 text-purple-400 rounded border border-purple-700/30">
                  Risk-Optimized
                </span>
              </div>
            </div>

            {/* Hedging Module */}
            <div className="p-5 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white">Delta Hedging Module</h3>
                <TrendingUp className="h-5 w-5 text-amber-400" />
              </div>
              <p className="text-sm text-slate-400 mb-3 leading-relaxed">
                Automated risk management system that hedges impermanent loss exposure through 
                perpetual futures positions, maintaining delta-neutral or near-neutral positions.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 text-xs bg-emerald-900/20 text-emerald-400 rounded border border-emerald-700/30">
                  Delta Neutral
                </span>
                <span className="px-2 py-1 text-xs bg-blue-900/20 text-blue-400 rounded border border-blue-700/30">
                  IL Protection
                </span>
                <span className="px-2 py-1 text-xs bg-purple-900/20 text-purple-400 rounded border border-purple-700/30">
                  Automated
                </span>
              </div>
            </div>

            {/* Risk Analytics */}
            <div className="p-5 bg-slate-900/50 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white">Risk Analytics Engine</h3>
                <Shield className="h-5 w-5 text-red-400" />
              </div>
              <p className="text-sm text-slate-400 mb-3 leading-relaxed">
                Real-time risk monitoring and analysis system calculating VaR, volatility, 
                Sharpe ratio, and other metrics to ensure positions stay within risk parameters.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 text-xs bg-emerald-900/20 text-emerald-400 rounded border border-emerald-700/30">
                  VaR/CVaR
                </span>
                <span className="px-2 py-1 text-xs bg-blue-900/20 text-blue-400 rounded border border-blue-700/30">
                  Real-time
                </span>
                <span className="px-2 py-1 text-xs bg-purple-900/20 text-purple-400 rounded border border-purple-700/30">
                  Risk Limits
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* External Resources */}
        <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2 mb-6">
            <ExternalLink className="h-6 w-6 text-emerald-400" />
            External Resources
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a
              href="https://docs.aster.finance"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-emerald-600 transition-colors group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-blue-400" />
                  <h3 className="font-semibold text-white">Aster Protocol Docs</h3>
                </div>
                <ExternalLink className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition-colors" />
              </div>
              <p className="text-sm text-slate-400">
                Official documentation for Aster Protocol integration
              </p>
            </a>

            <a
              href="https://pancakeswap.finance/info"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-emerald-600 transition-colors group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <Layers className="h-5 w-5 text-purple-400" />
                  <h3 className="font-semibold text-white">PancakeSwap Analytics</h3>
                </div>
                <ExternalLink className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition-colors" />
              </div>
              <p className="text-sm text-slate-400">
                Pool analytics and liquidity data
              </p>
            </a>

            <a
              href="https://eips.ethereum.org/EIPS/eip-4626"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-emerald-600 transition-colors group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <Code className="h-5 w-5 text-emerald-400" />
                  <h3 className="font-semibold text-white">ERC-4626 Standard</h3>
                </div>
                <ExternalLink className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition-colors" />
              </div>
              <p className="text-sm text-slate-400">
                Tokenized vault standard specification
              </p>
            </a>

            <a
              href="https://bscscan.com"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-emerald-600 transition-colors group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <Shield className="h-5 w-5 text-amber-400" />
                  <h3 className="font-semibold text-white">BscScan Explorer</h3>
                </div>
                <ExternalLink className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition-colors" />
              </div>
              <p className="text-sm text-slate-400">
                Verify contract code and transactions
              </p>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
