export interface ContractAddress {
  address: string;
  abi?: any[];
}

export interface TokenConfig {
  address: string;
  symbol: string;
  name: string;
  decimals: number;
  icon?: string;
}

export interface ChainConfig {
  id: number;
  name: string;
  rpcUrl: string;
  blockExplorer: string;
  nativeCurrency: {
    name: string;
    symbol: string;
    decimals: number;
  };
}

// Contract Addresses
export const CONTRACTS = {
  ASTER_EARN_VAULT: {
    address: process.env.NEXT_PUBLIC_ASTER_EARN_VAULT_ADDRESS || '0x0000000000000000000000000000000000000000',
  },
  STACK_ROUTER: {
    address: process.env.NEXT_PUBLIC_STACK_ROUTER_ADDRESS || '0x0000000000000000000000000000000000000000',
  },
  STRATEGY_CONTROLLER: {
    address: process.env.NEXT_PUBLIC_STRATEGY_CONTROLLER_ADDRESS || '0x0000000000000000000000000000000000000000',
  },
  PANCAKE_LP_MANAGER: {
    address: process.env.NEXT_PUBLIC_PANCAKE_LP_MANAGER_ADDRESS || '0x0000000000000000000000000000000000000000',
  },
} as const;

// Token Configurations
export const TOKENS: Record<string, TokenConfig> = {
  WBNB: {
    address: process.env.NEXT_PUBLIC_WBNB_ADDRESS || '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
    symbol: 'WBNB',
    name: 'Wrapped BNB',
    decimals: 18,
    icon: '/tokens/bnb.svg',
  },
  USDT: {
    address: process.env.NEXT_PUBLIC_USDT_ADDRESS || '0x55d398326f99059fF775485246999027B3197955',
    symbol: 'USDT',
    name: 'Tether USD',
    decimals: 18,
    icon: '/tokens/usdt.svg',
  },
  BUSD: {
    address: process.env.NEXT_PUBLIC_BUSD_ADDRESS || '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
    symbol: 'BUSD',
    name: 'Binance USD',
    decimals: 18,
    icon: '/tokens/busd.svg',
  },
} as const;

// Chain Configurations
export const CHAIN_CONFIG: Record<string, ChainConfig> = {
  mainnet: {
    id: parseInt(process.env.NEXT_PUBLIC_CHAIN_ID || '56'),
    name: 'BNB Smart Chain',
    rpcUrl: process.env.NEXT_PUBLIC_BNB_RPC_URL || 'https://bsc-dataseed.binance.org/',
    blockExplorer: 'https://bscscan.com',
    nativeCurrency: {
      name: 'BNB',
      symbol: 'BNB',
      decimals: 18,
    },
  },
  testnet: {
    id: parseInt(process.env.NEXT_PUBLIC_TESTNET_CHAIN_ID || '97'),
    name: 'BNB Smart Chain Testnet',
    rpcUrl: process.env.NEXT_PUBLIC_BNB_TESTNET_RPC_URL || 'https://data-seed-prebsc-1-s1.binance.org:8545/',
    blockExplorer: 'https://testnet.bscscan.com',
    nativeCurrency: {
      name: 'BNB',
      symbol: 'BNB',
      decimals: 18,
    },
  },
} as const;

// Helper function to check if a contract is deployed
export const isContractDeployed = (contractAddress: string): boolean => {
  const zeroAddress = '0x0000000000000000000000000000000000000000';
  return contractAddress !== zeroAddress && contractAddress.length === 42 && contractAddress.startsWith('0x');
};

// Helper to get current chain config
export const getCurrentChainConfig = (): ChainConfig => {
  const chainId = parseInt(process.env.NEXT_PUBLIC_CHAIN_ID || '56');
  return chainId === 97 ? CHAIN_CONFIG.testnet : CHAIN_CONFIG.mainnet;
};

// Export all contract addresses as array for easy iteration
export const getAllContracts = () => Object.entries(CONTRACTS).map(([name, config]) => ({
  name,
  ...config,
  deployed: isContractDeployed(config.address),
}));
