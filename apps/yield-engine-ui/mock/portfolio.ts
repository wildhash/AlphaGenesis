export interface PortfolioPosition {
  id: string;
  protocol: string;
  type: 'Earn' | 'LP' | 'Farm';
  depositedAmount: number;
  currentValue: number;
  yieldEarned: number;
  apy: number;
  tokens: string[];
}

export interface PortfolioData {
  totalDeposits: number;
  totalValue: number;
  totalShares: number;
  totalYieldEarned: number;
  totalPnL: number;
  pnlPercentage: number;
  positions: PortfolioPosition[];
  depositHistory: {
    timestamp: number;
    amount: number;
    txHash: string;
  }[];
  yieldHistory: {
    timestamp: number;
    amount: number;
    source: string;
  }[];
}

export const mockPortfolio: PortfolioData = {
  totalDeposits: 125000.00,
  totalValue: 142750.50,
  totalShares: 1250000,
  totalYieldEarned: 17750.50,
  totalPnL: 17750.50,
  pnlPercentage: 14.20,
  positions: [
    {
      id: 'pos-1',
      protocol: 'AsterEarn',
      type: 'Earn',
      depositedAmount: 50000.00,
      currentValue: 56250.00,
      yieldEarned: 6250.00,
      apy: 12.5,
      tokens: ['USDT', 'BUSD'],
    },
    {
      id: 'pos-2',
      protocol: 'PancakeSwap',
      type: 'LP',
      depositedAmount: 45000.00,
      currentValue: 51975.50,
      yieldEarned: 6975.50,
      apy: 15.5,
      tokens: ['WBNB', 'USDT'],
    },
    {
      id: 'pos-3',
      protocol: 'PancakeSwap',
      type: 'Farm',
      depositedAmount: 30000.00,
      currentValue: 34525.00,
      yieldEarned: 4525.00,
      apy: 15.08,
      tokens: ['CAKE', 'BNB'],
    },
  ],
  depositHistory: [
    {
      timestamp: Date.now() - 90 * 24 * 60 * 60 * 1000, // 90 days ago
      amount: 50000.00,
      txHash: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    },
    {
      timestamp: Date.now() - 60 * 24 * 60 * 60 * 1000, // 60 days ago
      amount: 45000.00,
      txHash: '0x2234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    },
    {
      timestamp: Date.now() - 30 * 24 * 60 * 60 * 1000, // 30 days ago
      amount: 30000.00,
      txHash: '0x3234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    },
  ],
  yieldHistory: [
    {
      timestamp: Date.now() - 7 * 24 * 60 * 60 * 1000,
      amount: 450.25,
      source: 'AsterEarn',
    },
    {
      timestamp: Date.now() - 14 * 24 * 60 * 60 * 1000,
      amount: 520.75,
      source: 'PancakeSwap LP',
    },
    {
      timestamp: Date.now() - 21 * 24 * 60 * 60 * 1000,
      amount: 380.50,
      source: 'PancakeSwap Farm',
    },
    {
      timestamp: Date.now() - 28 * 24 * 60 * 60 * 1000,
      amount: 425.00,
      source: 'AsterEarn',
    },
  ],
};
