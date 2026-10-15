'use client';

import { useAccount, useChainId } from 'wagmi';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import { bsc, bscTestnet } from 'wagmi/chains';

const SUPPORTED_CHAINS = [bsc.id, bscTestnet.id] as const;

export function NetworkBadge() {
  const { isConnected } = useAccount();
  const chainId = useChainId();

  if (!isConnected) {
    return null;
  }

  const isSupported = (SUPPORTED_CHAINS as readonly number[]).includes(chainId);
  const networkName = chainId === bsc.id 
    ? 'BNB Mainnet' 
    : chainId === bscTestnet.id 
    ? 'BNB Testnet' 
    : 'Wrong Network';

  return (
    <div className="inline-flex items-center gap-2">
      {isSupported ? (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-950/50 text-emerald-400 rounded-full border border-emerald-800/50">
          <CheckCircle2 className="w-4 h-4" />
          <span className="text-sm font-medium">{networkName}</span>
        </div>
      ) : (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-red-950/50 text-red-400 rounded-full border border-red-800/50">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm font-medium">{networkName}</span>
        </div>
      )}
    </div>
  );
}
