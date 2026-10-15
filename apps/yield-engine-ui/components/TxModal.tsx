'use client';

import { useState } from 'react';
import { X, AlertCircle, ArrowDownCircle, ArrowUpCircle, CheckCircle } from 'lucide-react';

interface TxModalProps {
  isOpen: boolean;
  onClose: () => void;
  type: 'deposit' | 'withdraw';
}

export function TxModal({ isOpen, onClose, type }: TxModalProps) {
  const [amount, setAmount] = useState('');
  const [isApproved, setIsApproved] = useState(false);
  const [txStatus, setTxStatus] = useState<'idle' | 'approving' | 'confirming' | 'success'>('idle');

  if (!isOpen) return null;

  const handleApprove = () => {
    setTxStatus('approving');
    setTimeout(() => {
      setIsApproved(true);
      setTxStatus('idle');
    }, 1500);
  };

  const handleConfirm = () => {
    setTxStatus('confirming');
    setTimeout(() => {
      setTxStatus('success');
      setTimeout(() => {
        onClose();
        setAmount('');
        setIsApproved(false);
        setTxStatus('idle');
      }, 2000);
    }, 2000);
  };

  const isDeposit = type === 'deposit';
  const title = isDeposit ? 'Deposit to Vault' : 'Withdraw from Vault';
  const Icon = isDeposit ? ArrowDownCircle : ArrowUpCircle;
  const iconColor = isDeposit ? 'text-emerald-500' : 'text-amber-500';
  const buttonColor = isDeposit ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-amber-600 hover:bg-amber-700';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-md bg-slate-900 rounded-xl shadow-2xl border border-slate-700 mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-slate-800`}>
              <Icon className={`h-6 w-6 ${iconColor}`} />
            </div>
            <h2 className="text-xl font-bold text-white">{title}</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Mock Mode Warning */}
          <div className="flex items-start gap-3 p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg">
            <AlertCircle className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="text-blue-300 font-medium">Mock Mode Active</p>
              <p className="text-blue-400/80 mt-1">
                Contracts not yet deployed. This is a UI preview with simulated transactions.
              </p>
            </div>
          </div>

          {/* Amount Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-300">
              Amount (USDT)
            </label>
            <div className="relative">
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                disabled={txStatus !== 'idle'}
              />
              <button
                onClick={() => setAmount('1000')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
                disabled={txStatus !== 'idle'}
              >
                MAX
              </button>
            </div>
          </div>

          {/* Transaction Summary */}
          {amount && parseFloat(amount) > 0 && (
            <div className="space-y-3 p-4 bg-slate-800 rounded-lg border border-slate-700">
              <h3 className="text-sm font-medium text-slate-300">Transaction Summary</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Amount</span>
                  <span className="text-white font-medium">{parseFloat(amount).toLocaleString()} USDT</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Estimated Shares</span>
                  <span className="text-white font-medium">
                    {(parseFloat(amount) * 10).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Current APY</span>
                  <span className="text-emerald-400 font-medium">12.5%</span>
                </div>
                <div className="flex justify-between pt-2 border-t border-slate-700">
                  <span className="text-slate-400">Gas Fee (estimated)</span>
                  <span className="text-slate-300">~$0.50</span>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="space-y-3">
            {!isApproved ? (
              <button
                onClick={handleApprove}
                disabled={!amount || parseFloat(amount) <= 0 || txStatus !== 'idle'}
                className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-all duration-200 ${
                  amount && parseFloat(amount) > 0 && txStatus === 'idle'
                    ? 'bg-slate-700 hover:bg-slate-600'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                }`}
              >
                {txStatus === 'approving' ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="h-4 w-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    Approving...
                  </span>
                ) : (
                  'Approve USDT'
                )}
              </button>
            ) : (
              <div className="flex items-center justify-center gap-2 py-3 px-4 bg-emerald-900/20 border border-emerald-700/30 rounded-lg text-emerald-400">
                <CheckCircle className="h-4 w-4" />
                <span className="text-sm font-medium">Token Approved</span>
              </div>
            )}

            <button
              onClick={handleConfirm}
              disabled={!isApproved || !amount || parseFloat(amount) <= 0 || txStatus !== 'idle'}
              className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-all duration-200 ${
                isApproved && amount && parseFloat(amount) > 0 && txStatus === 'idle'
                  ? `${buttonColor} shadow-lg`
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'
              }`}
            >
              {txStatus === 'confirming' ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="h-4 w-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  Processing...
                </span>
              ) : txStatus === 'success' ? (
                <span className="flex items-center justify-center gap-2">
                  <CheckCircle className="h-4 w-4" />
                  Success!
                </span>
              ) : (
                `Confirm ${isDeposit ? 'Deposit' : 'Withdrawal'}`
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
