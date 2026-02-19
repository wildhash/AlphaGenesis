'use client';

import { CheckCircle2, Clock, Shield, Lock, Code, FileText, Eye, Users } from 'lucide-react';

interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  status: 'completed' | 'pending' | 'in-progress';
  icon: React.ReactNode;
}

const securityChecklist: ChecklistItem[] = [
  {
    id: 'no-admin-keys',
    title: 'No Admin Keys',
    description: 'Protocol operates without privileged admin access or owner keys that could modify parameters or steal funds.',
    status: 'completed',
    icon: <Lock className="h-5 w-5" />,
  },
  {
    id: 'immutable-params',
    title: 'Immutable Parameters',
    description: 'Core protocol parameters are set at deployment and cannot be changed, ensuring predictable behavior.',
    status: 'completed',
    icon: <Shield className="h-5 w-5" />,
  },
  {
    id: 'no-offchain',
    title: 'No Off-Chain Triggers',
    description: 'All protocol logic executes on-chain without relying on external keepers or off-chain oracles.',
    status: 'completed',
    icon: <Code className="h-5 w-5" />,
  },
  {
    id: 'open-source',
    title: 'Open Source Code',
    description: 'All smart contract code is publicly available and verifiable on blockchain explorers.',
    status: 'completed',
    icon: <Eye className="h-5 w-5" />,
  },
  {
    id: 'non-custodial',
    title: 'Non-Custodial',
    description: 'Users maintain full control of their assets. The protocol never takes custody of user funds.',
    status: 'completed',
    icon: <Users className="h-5 w-5" />,
  },
  {
    id: 'audit-pending',
    title: 'Security Audit',
    description: 'Professional third-party security audit by reputable firm. Comprehensive review of all smart contracts.',
    status: 'pending',
    icon: <FileText className="h-5 w-5" />,
  },
  {
    id: 'bug-bounty',
    title: 'Bug Bounty Program',
    description: 'Active bug bounty program to incentivize responsible disclosure of vulnerabilities.',
    status: 'pending',
    icon: <Shield className="h-5 w-5" />,
  },
  {
    id: 'timelock',
    title: 'Upgrade Timelock',
    description: 'Any future protocol upgrades require a time delay, giving users notice to exit if desired.',
    status: 'in-progress',
    icon: <Clock className="h-5 w-5" />,
  },
];

export function AuditChecklist() {
  const getStatusBadge = (status: ChecklistItem['status']) => {
    switch (status) {
      case 'completed':
        return (
          <span className="px-3 py-1 text-xs font-medium rounded-full bg-emerald-900/20 text-emerald-400 border border-emerald-700/30">
            Implemented
          </span>
        );
      case 'in-progress':
        return (
          <span className="px-3 py-1 text-xs font-medium rounded-full bg-yellow-900/20 text-yellow-400 border border-yellow-700/30">
            In Progress
          </span>
        );
      case 'pending':
        return (
          <span className="px-3 py-1 text-xs font-medium rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            Coming Soon
          </span>
        );
    }
  };

  const getIconColor = (status: ChecklistItem['status']) => {
    switch (status) {
      case 'completed':
        return 'text-emerald-400';
      case 'in-progress':
        return 'text-yellow-400';
      case 'pending':
        return 'text-slate-500';
    }
  };

  const completedCount = securityChecklist.filter(item => item.status === 'completed').length;
  const totalCount = securityChecklist.length;
  const completionPercentage = Math.round((completedCount / totalCount) * 100);

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800">
      <div className="px-6 py-4 border-b border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Shield className="h-5 w-5 text-emerald-400" />
            Security Checklist
          </h3>
          <div className="text-sm text-slate-400">
            {completedCount}/{totalCount} Complete
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="mt-3">
          <div className="w-full bg-slate-800 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-emerald-500 to-emerald-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {completionPercentage}% security features implemented
          </p>
        </div>
      </div>

      <div className="p-6">
        <div className="space-y-4">
          {securityChecklist.map((item) => (
            <div
              key={item.id}
              className="p-4 bg-slate-800/30 rounded-lg border border-slate-700 hover:border-slate-600 transition-colors"
            >
              <div className="flex items-start gap-4">
                <div className={`p-2 rounded-lg ${
                  item.status === 'completed' ? 'bg-emerald-900/20' :
                  item.status === 'in-progress' ? 'bg-yellow-900/20' :
                  'bg-slate-800'
                } ${getIconColor(item.status)}`}>
                  {item.status === 'completed' ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                  ) : (
                    item.icon
                  )}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <h4 className="font-medium text-white">{item.title}</h4>
                    {getStatusBadge(item.status)}
                  </div>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Important Notice */}
        <div className="mt-6 p-4 bg-blue-950/30 border border-blue-800/50 rounded-lg">
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="font-medium text-blue-300 mb-1">
                Security First Approach
              </div>
              <p className="text-sm text-blue-200/80">
                We prioritize security and transparency. While some features are still pending, 
                we&apos;ve implemented core security measures including non-custodial architecture, 
                immutable parameters, and no admin keys. Professional audits are scheduled before mainnet launch.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
