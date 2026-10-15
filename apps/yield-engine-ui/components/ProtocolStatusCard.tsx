'use client';

import { getAllContracts } from '@/config/contracts';
import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { useAccount } from 'wagmi';

export function ProtocolStatusCard() {
  const { isConnected } = useAccount();
  const contracts = getAllContracts();
  const deployedCount = contracts.filter(c => c.deployed).length;
  const totalCount = contracts.length;
  const allDeployed = deployedCount === totalCount;

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-xl overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800">
        <h3 className="text-lg font-semibold text-white">Protocol Status</h3>
        <p className="text-sm text-slate-400 mt-1">
          Smart contract deployment status
        </p>
      </div>

      <div className="p-6 space-y-4">
        {/* Overall Status */}
        <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
          <div className="flex items-center gap-3">
            {allDeployed ? (
              <CheckCircle2 className="w-6 h-6 text-emerald-500" />
            ) : (
              <AlertTriangle className="w-6 h-6 text-yellow-500" />
            )}
            <div>
              <div className="font-medium text-white">
                {allDeployed ? 'All Contracts Deployed' : 'Partial Deployment'}
              </div>
              <div className="text-sm text-slate-400">
                {deployedCount} of {totalCount} contracts deployed
              </div>
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-500">
            {deployedCount}/{totalCount}
          </div>
        </div>

        {/* Mock Mode Warning */}
        {!allDeployed && (
          <div className="flex items-start gap-3 p-4 bg-yellow-950/30 border border-yellow-800/50 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="font-medium text-yellow-400 mb-1">Mock Mode Active</div>
              <p className="text-sm text-yellow-300/80">
                Some contracts are not deployed. The UI will display mock data for testing purposes.
                Connect to a network with deployed contracts for full functionality.
              </p>
            </div>
          </div>
        )}

        {/* Contract List */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-slate-300 mb-3">Contract Addresses</h4>
          {contracts.map((contract) => (
            <div
              key={contract.name}
              className="flex items-center justify-between p-3 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                {contract.deployed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-slate-600 flex-shrink-0" />
                )}
                <span className="text-sm font-medium text-white">
                  {contract.name.replace(/_/g, ' ')}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {contract.deployed ? (
                  <code className="text-xs text-emerald-400 bg-emerald-950/50 px-2 py-1 rounded font-mono">
                    {contract.address.slice(0, 6)}...{contract.address.slice(-4)}
                  </code>
                ) : (
                  <span className="text-xs text-slate-500 italic">Not deployed</span>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Connection Status */}
        <div className="pt-4 border-t border-slate-800">
          <div className="flex items-center gap-2 text-sm">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-slate-600'}`} />
            <span className="text-slate-400">
              {isConnected ? 'Wallet Connected' : 'Wallet Not Connected'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
