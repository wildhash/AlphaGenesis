'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Menu, X, Zap } from 'lucide-react';
import { WalletConnectButton } from './WalletConnectButton';
import { NetworkBadge } from './NetworkBadge';

const navigation = [
  { name: 'Dashboard', href: '/dashboard' },
  { name: 'Strategy', href: '/strategy' },
  { name: 'Positions', href: '/positions' },
  { name: 'Risk', href: '/risk' },
  { name: 'Docs', href: '/docs' },
];

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-slate-950/90 backdrop-blur-md border-b border-emerald-900/20">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8" aria-label="Global">
        {/* Logo */}
        <div className="flex lg:flex-1">
          <Link href="/" className="-m-1.5 p-1.5 flex items-center gap-2 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-600 to-emerald-800 shadow-lg group-hover:shadow-emerald-600/50 transition-all duration-200">
              <Zap className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white group-hover:text-emerald-400 transition-colors">
              AlphaGenesis
            </span>
          </Link>
        </div>

        {/* Mobile menu button */}
        <div className="flex lg:hidden">
          <button
            type="button"
            className="-m-2.5 inline-flex items-center justify-center rounded-md p-2.5 text-slate-400 hover:text-emerald-400"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <span className="sr-only">Toggle main menu</span>
            {mobileMenuOpen ? (
              <X className="h-6 w-6" aria-hidden="true" />
            ) : (
              <Menu className="h-6 w-6" aria-hidden="true" />
            )}
          </button>
        </div>

        {/* Desktop navigation */}
        <div className="hidden lg:flex lg:gap-x-8">
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className="text-sm font-semibold leading-6 text-slate-300 hover:text-emerald-400 transition-colors"
            >
              {item.name}
            </Link>
          ))}
        </div>

        {/* Wallet and Network */}
        <div className="hidden lg:flex lg:flex-1 lg:justify-end lg:items-center lg:gap-3">
          <NetworkBadge />
          <WalletConnectButton />
        </div>
      </nav>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden">
          <div className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-sm">
            <div className="fixed inset-y-0 right-0 z-50 w-full overflow-y-auto bg-slate-950 px-6 py-6 sm:max-w-sm sm:ring-1 sm:ring-emerald-900/10">
              <div className="flex items-center justify-between">
                <Link href="/" className="-m-1.5 p-1.5 flex items-center gap-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-600 to-emerald-800 shadow-lg">
                    <Zap className="h-6 w-6 text-white" />
                  </div>
                  <span className="text-xl font-bold text-white">AlphaGenesis</span>
                </Link>
                <button
                  type="button"
                  className="-m-2.5 rounded-md p-2.5 text-slate-400 hover:text-emerald-400"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <span className="sr-only">Close menu</span>
                  <X className="h-6 w-6" aria-hidden="true" />
                </button>
              </div>
              <div className="mt-6 flow-root">
                <div className="-my-6 divide-y divide-slate-800">
                  <div className="space-y-2 py-6">
                    {navigation.map((item) => (
                      <Link
                        key={item.name}
                        href={item.href}
                        className="-mx-3 block rounded-lg px-3 py-2 text-base font-semibold leading-7 text-slate-300 hover:bg-slate-900 hover:text-emerald-400"
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        {item.name}
                      </Link>
                    ))}
                  </div>
                  <div className="py-6 space-y-4">
                    <NetworkBadge />
                    <WalletConnectButton />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
