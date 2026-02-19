export interface Position {
  id: string;
  type: 'Earn' | 'LP' | 'Farm';
  protocol: string;
  tokens: string[];
  depositedAmount: number;
  currentValue: number;
  apy: number;
  pnl: number;
  pnlPercentage: number;
  health: number; // 0-100, health score of the position
  status: 'active' | 'closed' | 'pending';
  entryDate: number;
  lastUpdate: number;
  metadata?: {
    poolAddress?: string;
    farmId?: number;
    vaultId?: string;
    lpTokenBalance?: string;
  };
}

export const mockPositions: Position[] = [
  {
    id: 'pos-earn-001',
    type: 'Earn',
    protocol: 'AsterEarn',
    tokens: ['USDT', 'BUSD'],
    depositedAmount: 50000.00,
    currentValue: 56250.00,
    apy: 12.5,
    pnl: 6250.00,
    pnlPercentage: 12.50,
    health: 95,
    status: 'active',
    entryDate: Date.now() - 90 * 24 * 60 * 60 * 1000,
    lastUpdate: Date.now() - 60 * 1000,
    metadata: {
      vaultId: 'vault-001',
    },
  },
  {
    id: 'pos-lp-001',
    type: 'LP',
    protocol: 'PancakeSwap',
    tokens: ['WBNB', 'USDT'],
    depositedAmount: 45000.00,
    currentValue: 51975.50,
    apy: 15.5,
    pnl: 6975.50,
    pnlPercentage: 15.50,
    health: 88,
    status: 'active',
    entryDate: Date.now() - 60 * 24 * 60 * 60 * 1000,
    lastUpdate: Date.now() - 120 * 1000,
    metadata: {
      poolAddress: '0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae',
      lpTokenBalance: '1.234567890123456789',
    },
  },
  {
    id: 'pos-farm-001',
    type: 'Farm',
    protocol: 'PancakeSwap',
    tokens: ['CAKE', 'BNB'],
    depositedAmount: 30000.00,
    currentValue: 34525.00,
    apy: 15.08,
    pnl: 4525.00,
    pnlPercentage: 15.08,
    health: 92,
    status: 'active',
    entryDate: Date.now() - 30 * 24 * 60 * 60 * 1000,
    lastUpdate: Date.now() - 90 * 1000,
    metadata: {
      farmId: 42,
      lpTokenBalance: '0.987654321098765432',
    },
  },
  {
    id: 'pos-lp-002',
    type: 'LP',
    protocol: 'PancakeSwap',
    tokens: ['BUSD', 'USDT'],
    depositedAmount: 25000.00,
    currentValue: 26125.00,
    apy: 4.5,
    pnl: 1125.00,
    pnlPercentage: 4.50,
    health: 98,
    status: 'active',
    entryDate: Date.now() - 45 * 24 * 60 * 60 * 1000,
    lastUpdate: Date.now() - 180 * 1000,
    metadata: {
      poolAddress: '0x7efaef62fddcca950418312c6c91aef321375a00',
      lpTokenBalance: '2.345678901234567890',
    },
  },
  {
    id: 'pos-earn-002',
    type: 'Earn',
    protocol: 'AsterEarn',
    tokens: ['WBNB'],
    depositedAmount: 15000.00,
    currentValue: 16350.00,
    apy: 9.0,
    pnl: 1350.00,
    pnlPercentage: 9.00,
    health: 90,
    status: 'active',
    entryDate: Date.now() - 20 * 24 * 60 * 60 * 1000,
    lastUpdate: Date.now() - 240 * 1000,
    metadata: {
      vaultId: 'vault-002',
    },
  },
  {
    id: 'pos-farm-002',
    type: 'Farm',
    protocol: 'PancakeSwap',
    tokens: ['ETH', 'BNB'],
    depositedAmount: 35000.00,
    currentValue: 38150.00,
    apy: 18.0,
    pnl: 3150.00,
    pnlPercentage: 9.00,
    health: 85,
    status: 'active',
    entryDate: Date.now() - 25 * 24 * 60 * 60 * 1000,
    lastUpdate: Date.now() - 300 * 1000,
    metadata: {
      farmId: 73,
      lpTokenBalance: '1.456789012345678901',
    },
  },
  {
    id: 'pos-lp-003',
    type: 'LP',
    protocol: 'PancakeSwap',
    tokens: ['CAKE', 'BUSD'],
    depositedAmount: 20000.00,
    currentValue: 19200.00,
    apy: 8.2,
    pnl: -800.00,
    pnlPercentage: -4.00,
    health: 72,
    status: 'active',
    entryDate: Date.now() - 15 * 24 * 60 * 60 * 1000,
    lastUpdate: Date.now() - 360 * 1000,
    metadata: {
      poolAddress: '0x804678fa97d91b974ec2af3c843270886528a9e6',
      lpTokenBalance: '0.765432109876543210',
    },
  },
];

// Helper functions
export const getPositionsByType = (type: Position['type']): Position[] => {
  return mockPositions.filter(pos => pos.type === type);
};

export const getPositionsByProtocol = (protocol: string): Position[] => {
  return mockPositions.filter(pos => pos.protocol === protocol);
};

export const getActivePositions = (): Position[] => {
  return mockPositions.filter(pos => pos.status === 'active');
};

export const getTotalPnL = (): number => {
  return mockPositions.reduce((sum, pos) => sum + pos.pnl, 0);
};

export const getTotalValue = (): number => {
  return mockPositions.reduce((sum, pos) => sum + pos.currentValue, 0);
};

export const getAverageHealth = (): number => {
  const activePositions = getActivePositions();
  const totalHealth = activePositions.reduce((sum, pos) => sum + pos.health, 0);
  return activePositions.length > 0 ? totalHealth / activePositions.length : 0;
};
