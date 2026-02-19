'use client';

import { useState } from 'react';
import { 
  ArrowRight,
  Shield,
  TrendingUp,
  RefreshCw,
  Zap,
  Lock,
  Activity,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Layers
} from 'lucide-react';

export default function StrategyPage() {
  const [activeScenario, setActiveScenario] = useState<'volatility' | 'liquidation' | 'exploit'>('volatility');

  const flowSteps = [
    {
      id: 1,
      title: 'User Deposit',
      description: 'Users deposit stablecoins (USDT, BUSD) into the vault',
      icon: Lock,
      color: 'from-blue-600 to-blue-800',
      details: [
        'Non-custodial vault contract',
        'Mint vault shares proportional to deposit',
        'No admin keys or backdoors',
        'Instant liquidity available'
      ]
    },
    {
      id: 2,
      title: 'AsterDEX Earn',
      description: 'Funds deployed to AsterDEX lending protocol',
      icon: Zap,
      color: 'from-emerald-600 to-emerald-800',
      details: [
        'Automated lending on AsterDEX',
        'Base yield generation starts',
        'Low-risk stablecoin markets',
        'Real-time APY tracking'
      ]
    },
    {
      id: 3,
      title: 'Stack Router',
      description: 'Yield routed through Stack for additional opportunities',
      icon: Layers,
      color: 'from-purple-600 to-purple-800',
      details: [
        'Smart routing to highest yields',
        'Composability layer integration',
        'Automatic rebalancing',
        'Gas optimization'
      ]
    },
    {
      id: 4,
      title: 'PancakeSwap LP/Farm',
      description: 'LP positions and farming for amplified returns',
      icon: BarChart3,
      color: 'from-amber-600 to-amber-800',
      details: [
        'Liquidity provision on PCS',
        'Farm CAKE and other rewards',
        'Impermanent loss monitoring',
        'Auto-compounding rewards'
      ]
    },
    {
      id: 5,
      title: 'Delta-Neutral Hedging',
      description: 'Risk protection through automated hedging',
      icon: Shield,
      color: 'from-red-600 to-red-800',
      details: [
        'Perpetual futures hedging',
        'Delta-neutral positioning',
        'Volatility protection',
        'Continuous rebalancing'
      ]
    },
    {
      id: 6,
      title: 'Yield Distribution',
      description: 'Returns flow back to vault shares',
      icon: TrendingUp,
      color: 'from-emerald-600 to-emerald-800',
      details: [
        'Automatic compounding',
        'Share value appreciation',
        'Transparent accounting',
        'Withdraw anytime'
      ]
    }
  ];

  const scenarios = {
    volatility: {
      title: 'High Volatility Event',
      description: 'What happens when crypto markets experience extreme volatility?',
      icon: Activity,
      color: 'text-amber-400',
      steps: [
        {
          action: 'Market volatility detected',
          response: 'Automated hedging triggers immediately',
          icon: AlertTriangle
        },
        {
          action: 'Asset prices swing dramatically',
          response: 'Delta-neutral hedges protect principal',
          icon: Shield
        },
        {
          action: 'IL risk increases in LP positions',
          response: 'Rebalancer adjusts exposure automatically',
          icon: RefreshCw
        },
        {
          action: 'Yield opportunities shift',
          response: 'Stack Router redirects to safer yields',
          icon: Layers
        },
        {
          action: 'User confidence maintained',
          response: 'Transparent reporting, no surprises',
          icon: CheckCircle
        }
      ]
    },
    liquidation: {
      title: 'Liquidation Risk',
      description: 'How does the system handle potential liquidation scenarios?',
      icon: AlertTriangle,
      color: 'text-red-400',
      steps: [
        {
          action: 'Position health degrading',
          response: 'Health monitor triggers early warning',
          icon: Activity
        },
        {
          action: 'Collateral value dropping',
          response: 'Automatic position reduction begins',
          icon: TrendingUp
        },
        {
          action: 'Liquidation threshold approaching',
          response: 'Emergency exit protocol activates',
          icon: Shield
        },
        {
          action: 'Partial position closure needed',
          response: 'Minimize losses, preserve capital',
          icon: Lock
        },
        {
          action: 'Crisis averted',
          response: 'Resume normal operations gradually',
          icon: CheckCircle
        }
      ]
    },
    exploit: {
      title: 'Protocol Exploit Detection',
      description: 'Response to a potential exploit in an integrated protocol',
      icon: Shield,
      color: 'text-red-400',
      steps: [
        {
          action: 'Abnormal activity detected',
          response: 'Circuit breakers pause new deposits',
          icon: AlertTriangle
        },
        {
          action: 'Protocol compromise confirmed',
          response: 'Emergency withdrawal from affected protocol',
          icon: Shield
        },
        {
          action: 'Funds isolation needed',
          response: 'Assets moved to safe vault',
          icon: Lock
        },
        {
          action: 'User funds secured',
          response: 'Full transparency report published',
          icon: CheckCircle
        },
        {
          action: 'Recovery phase',
          response: 'Gradual redeployment to verified protocols',
          icon: RefreshCw
        }
      ]
    }
  };

  const activeScenarioData = scenarios[activeScenario];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-white mb-4">Yield Strategy Flow</h1>
          <p className="text-slate-400 text-lg max-w-3xl mx-auto">
            Automated, composable, and resilient yield optimization strategy built on BNB Chain
          </p>
        </div>

        {/* Strategy Flow */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-8 text-center">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {flowSteps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div key={step.id} className="relative">
                  {/* Flow Arrow (desktop only) */}
                  {idx < flowSteps.length - 1 && (
                    <div className="hidden lg:block absolute top-1/2 -right-3 z-10 transform -translate-y-1/2">
                      <ArrowRight className="h-6 w-6 text-emerald-500" />
                    </div>
                  )}
                  
                  <div className="h-full bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6 hover:border-emerald-700/50 transition-all">
                    <div className="flex items-center gap-3 mb-4">
                      <div className={`p-3 bg-gradient-to-br ${step.color} rounded-lg shadow-lg`}>
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="text-xs font-medium text-emerald-400 mb-1">
                          Step {step.id}
                        </div>
                        <h3 className="text-lg font-bold text-white">{step.title}</h3>
                      </div>
                    </div>
                    <p className="text-slate-400 text-sm mb-4">
                      {step.description}
                    </p>
                    <ul className="space-y-2">
                      {step.details.map((detail, detailIdx) => (
                        <li key={detailIdx} className="flex items-start gap-2 text-xs text-slate-300">
                          <CheckCircle className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                          <span>{detail}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Key Features */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-8 text-center">Core Principles</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
              <div className="p-3 bg-gradient-to-br from-emerald-600 to-emerald-800 rounded-lg w-fit mb-4">
                <Shield className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Non-Custodial</h3>
              <p className="text-slate-400 text-sm">
                Your funds remain in smart contracts you control. No admin keys, no backdoors, no third-party custody.
              </p>
            </div>

            <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
              <div className="p-3 bg-gradient-to-br from-purple-600 to-purple-800 rounded-lg w-fit mb-4">
                <Layers className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Composable</h3>
              <p className="text-slate-400 text-sm">
                Stack multiple DeFi protocols for amplified returns. AsterDEX → Stack → PancakeSwap seamlessly integrated.
              </p>
            </div>

            <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
              <div className="p-3 bg-gradient-to-br from-amber-600 to-amber-800 rounded-lg w-fit mb-4">
                <RefreshCw className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Self-Driving</h3>
              <p className="text-slate-400 text-sm">
                Fully automated rebalancing, hedging, and yield optimization. No manual intervention required.
              </p>
            </div>
          </div>
        </div>

        {/* Stress Scenarios */}
        <div>
          <h2 className="text-2xl font-bold text-white mb-8 text-center">What Happens During Stress?</h2>
          
          {/* Scenario Selector */}
          <div className="flex flex-wrap justify-center gap-4 mb-8">
            {Object.entries(scenarios).map(([key, scenario]) => {
              const Icon = scenario.icon;
              const isActive = activeScenario === key;
              return (
                <button
                  key={key}
                  onClick={() => setActiveScenario(key as typeof activeScenario)}
                  className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 text-white shadow-lg shadow-emerald-600/50'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
                  }`}
                >
                  <Icon className={`h-5 w-5 ${isActive ? 'text-white' : scenario.color}`} />
                  {scenario.title}
                </button>
              );
            })}
          </div>

          {/* Active Scenario */}
          <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-slate-800 rounded-lg">
                {(() => {
                  const Icon = activeScenarioData.icon;
                  return <Icon className={`h-6 w-6 ${activeScenarioData.color}`} />;
                })()}
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">{activeScenarioData.title}</h3>
                <p className="text-slate-400">{activeScenarioData.description}</p>
              </div>
            </div>

            <div className="space-y-4">
              {activeScenarioData.steps.map((step, idx) => {
                const Icon = step.icon;
                return (
                  <div
                    key={idx}
                    className="flex items-start gap-4 p-4 bg-slate-900/50 border border-slate-700 rounded-lg hover:border-emerald-700/50 transition-all"
                  >
                    <div className="flex items-center justify-center w-8 h-8 bg-slate-800 rounded-full text-emerald-400 font-bold text-sm flex-shrink-0">
                      {idx + 1}
                    </div>
                    <div className="flex-1 grid md:grid-cols-2 gap-4">
                      <div>
                        <div className="text-xs text-slate-500 font-medium mb-1">TRIGGER</div>
                        <p className="text-white font-medium">{step.action}</p>
                      </div>
                      <div>
                        <div className="text-xs text-emerald-400 font-medium mb-1">RESPONSE</div>
                        <div className="flex items-start gap-2">
                          <Icon className="h-4 w-4 text-emerald-400 flex-shrink-0 mt-1" />
                          <p className="text-slate-300">{step.response}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
