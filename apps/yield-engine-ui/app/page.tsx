import Link from "next/link";
import { Shield, Zap, Layers, Lock, TrendingUp, CheckCircle, ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-emerald-950">
      {/* Hero Section */}
      <section className="relative overflow-hidden px-6 py-24 sm:py-32 lg:px-8">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(45rem_50rem_at_top,theme(colors.emerald.900/20),transparent)]" />
        <div className="absolute inset-y-0 right-1/2 -z-10 mr-16 w-[200%] origin-bottom-left skew-x-[-30deg] bg-slate-900/80 shadow-xl shadow-emerald-900/10 ring-1 ring-emerald-900/10 sm:mr-28 lg:mr-0 xl:mr-16 xl:origin-center" />
        
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-2xl lg:mx-0">
            <h1 className="text-5xl font-bold tracking-tight text-white sm:text-7xl bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-emerald-600">
              Self-Driving Yield Engine
            </h1>
            <p className="mt-6 text-xl leading-8 text-slate-300">
              Autonomous yield optimization protocol on BNB Chain. Non-custodial, on-chain only, with no admin keys.
              Your capital, your control, our intelligence.
            </p>
            <div className="mt-10 flex items-center gap-x-6">
              <Link
                href="/dashboard"
                className="rounded-lg bg-emerald-600 px-6 py-3.5 text-base font-semibold text-white shadow-lg hover:bg-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 transition-all duration-200 flex items-center gap-2"
              >
                View Dashboard
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link href="#pillars" className="text-base font-semibold leading-7 text-emerald-400 hover:text-emerald-300 transition-colors">
                Learn more <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>

          {/* Stats */}
          <div className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-6 sm:mt-20 lg:mx-0 lg:max-w-none lg:grid-cols-3">
            <div className="flex flex-col gap-y-3 border border-emerald-900/30 bg-slate-900/50 px-6 py-8 rounded-2xl backdrop-blur-sm">
              <dt className="text-base leading-7 text-slate-400">Total Value Locked</dt>
              <dd className="text-3xl font-bold tracking-tight text-emerald-400">$0.00</dd>
            </div>
            <div className="flex flex-col gap-y-3 border border-emerald-900/30 bg-slate-900/50 px-6 py-8 rounded-2xl backdrop-blur-sm">
              <dt className="text-base leading-7 text-slate-400">Average APY</dt>
              <dd className="text-3xl font-bold tracking-tight text-emerald-400">--.--%</dd>
            </div>
            <div className="flex flex-col gap-y-3 border border-emerald-900/30 bg-slate-900/50 px-6 py-8 rounded-2xl backdrop-blur-sm">
              <dt className="text-base leading-7 text-slate-400">Active Strategies</dt>
              <dd className="text-3xl font-bold tracking-tight text-emerald-400">0</dd>
            </div>
          </div>
        </div>
      </section>

      {/* 4 Pillars Section */}
      <section id="pillars" className="px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-2xl lg:text-center mb-16">
            <h2 className="text-base font-semibold leading-7 text-emerald-400">The Foundation</h2>
            <p className="mt-2 text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Four Pillars of AlphaGenesis
            </p>
            <p className="mt-6 text-lg leading-8 text-slate-300">
              Built on principles that prioritize security, autonomy, and composability
            </p>
          </div>

          <div className="mx-auto grid max-w-2xl grid-cols-1 gap-8 lg:max-w-none lg:grid-cols-2">
            {/* Pillar 1: Integrate */}
            <div className="relative flex flex-col gap-6 rounded-2xl border border-emerald-900/30 bg-gradient-to-br from-slate-900/90 to-slate-900/50 p-8 backdrop-blur-sm hover:border-emerald-700/50 transition-all duration-300 hover:shadow-xl hover:shadow-emerald-900/20">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-900/30">
                  <Layers className="h-6 w-6 text-emerald-400" />
                </div>
                <h3 className="text-2xl font-semibold text-white">Integrate</h3>
              </div>
              <p className="text-base leading-7 text-slate-300">
                <span className="font-semibold text-emerald-400">AsterDEX Earn</span> as the foundation.
                Seamlessly integrate with BNB Chain&apos;s premier DeFi protocols to maximize yield opportunities.
              </p>
              <ul className="space-y-2 text-sm text-slate-400">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  Direct integration with AsterDEX
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  Multi-protocol yield aggregation
                </li>
              </ul>
            </div>

            {/* Pillar 2: Stack */}
            <div className="relative flex flex-col gap-6 rounded-2xl border border-emerald-900/30 bg-gradient-to-br from-slate-900/90 to-slate-900/50 p-8 backdrop-blur-sm hover:border-emerald-700/50 transition-all duration-300 hover:shadow-xl hover:shadow-emerald-900/20">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-900/30">
                  <TrendingUp className="h-6 w-6 text-emerald-400" />
                </div>
                <h3 className="text-2xl font-semibold text-white">Stack</h3>
              </div>
              <p className="text-base leading-7 text-slate-300">
                <span className="font-semibold text-emerald-400">Composability first.</span> Layer strategies
                to compound returns. Build complex yield optimization through simple, composable components.
              </p>
              <ul className="space-y-2 text-sm text-slate-400">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  Modular strategy building
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  Auto-compounding mechanisms
                </li>
              </ul>
            </div>

            {/* Pillar 3: Automate */}
            <div className="relative flex flex-col gap-6 rounded-2xl border border-emerald-900/30 bg-gradient-to-br from-slate-900/90 to-slate-900/50 p-8 backdrop-blur-sm hover:border-emerald-700/50 transition-all duration-300 hover:shadow-xl hover:shadow-emerald-900/20">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-900/30">
                  <Zap className="h-6 w-6 text-emerald-400" />
                </div>
                <h3 className="text-2xl font-semibold text-white">Automate</h3>
              </div>
              <p className="text-base leading-7 text-slate-300">
                <span className="font-semibold text-emerald-400">On-chain only.</span> Fully autonomous
                execution with no off-chain dependencies. Smart contracts handle everything from rebalancing to compounding.
              </p>
              <ul className="space-y-2 text-sm text-slate-400">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  Autonomous rebalancing
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  No manual intervention needed
                </li>
              </ul>
            </div>

            {/* Pillar 4: Protect */}
            <div className="relative flex flex-col gap-6 rounded-2xl border border-emerald-900/30 bg-gradient-to-br from-slate-900/90 to-slate-900/50 p-8 backdrop-blur-sm hover:border-emerald-700/50 transition-all duration-300 hover:shadow-xl hover:shadow-emerald-900/20">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-900/30">
                  <Shield className="h-6 w-6 text-emerald-400" />
                </div>
                <h3 className="text-2xl font-semibold text-white">Protect</h3>
              </div>
              <p className="text-base leading-7 text-slate-300">
                <span className="font-semibold text-emerald-400">Non-custodial.</span> You always control
                your funds. Built-in risk management, circuit breakers, and emergency withdrawal mechanisms.
              </p>
              <ul className="space-y-2 text-sm text-slate-400">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  Your keys, your crypto
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  Emergency withdrawal anytime
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Model Section */}
      <section className="px-6 py-24 sm:py-32 lg:px-8 bg-slate-900/50">
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-2xl lg:text-center mb-16">
            <h2 className="text-base font-semibold leading-7 text-emerald-400">Trust Model</h2>
            <p className="mt-2 text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Designed for Maximum Security
            </p>
          </div>

          <div className="mx-auto grid max-w-2xl grid-cols-1 gap-8 lg:max-w-none lg:grid-cols-3">
            <div className="flex flex-col gap-4 rounded-2xl border border-emerald-900/30 bg-slate-900/70 p-8 backdrop-blur-sm">
              <Lock className="h-10 w-10 text-emerald-400" />
              <h3 className="text-xl font-semibold text-white">No Admin Keys</h3>
              <p className="text-base text-slate-300">
                Zero admin privileges. Once deployed, contracts operate autonomously without any backdoors or admin control.
              </p>
            </div>

            <div className="flex flex-col gap-4 rounded-2xl border border-emerald-900/30 bg-slate-900/70 p-8 backdrop-blur-sm">
              <CheckCircle className="h-10 w-10 text-emerald-400" />
              <h3 className="text-xl font-semibold text-white">Deterministic</h3>
              <p className="text-base text-slate-300">
                All strategy logic is fully on-chain and verifiable. No hidden algorithms or off-chain oracle manipulation.
              </p>
            </div>

            <div className="flex flex-col gap-4 rounded-2xl border border-emerald-900/30 bg-slate-900/70 p-8 backdrop-blur-sm">
              <Shield className="h-10 w-10 text-emerald-400" />
              <h3 className="text-xl font-semibold text-white">Withdraw Anytime</h3>
              <p className="text-base text-slate-300">
                Users can withdraw their funds at any time. No lock-ups, no delays, no permission needed.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Ready to optimize your yield?
          </h2>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-300">
            Connect your wallet and start earning with AlphaGenesis. Join the future of autonomous DeFi on BNB Chain.
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <Link
              href="/dashboard"
              className="rounded-lg bg-emerald-600 px-8 py-4 text-lg font-semibold text-white shadow-lg hover:bg-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 transition-all duration-200 flex items-center gap-2"
            >
              Launch App
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/docs"
              className="text-lg font-semibold leading-7 text-emerald-400 hover:text-emerald-300 transition-colors"
            >
              Read Documentation <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
