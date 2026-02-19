# AsterDEX Self-Driving Yield Engine - UI Documentation

## Overview

This is a production-grade frontend/UI for a fully decentralized, non-custodial "Self-Driving Yield Engine" on BNB Chain that anchors on AsterDEX Earn. Built with Next.js 14, TypeScript, Tailwind CSS, and Web3 integration.

## 🏗️ Architecture

### Technology Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui patterns, lucide-react icons
- **Web3**: wagmi, viem, RainbowKit
- **Charts**: Recharts
- **Flow Diagrams**: @xyflow/react

### Project Structure

```
apps/yield-engine-ui/
├── app/                      # Next.js App Router pages
│   ├── layout.tsx           # Root layout with Web3Provider
│   ├── page.tsx             # Landing page
│   ├── dashboard/           # Portfolio overview
│   ├── strategy/            # Strategy visualization
│   ├── positions/           # Position management
│   ├── risk/                # Risk analytics
│   └── docs/                # Documentation
├── components/              # Reusable React components
│   ├── Header.tsx
│   ├── WalletConnectButton.tsx
│   ├── NetworkBadge.tsx
│   ├── ProtocolStatusCard.tsx
│   ├── TxModal.tsx
│   ├── PositionsTable.tsx
│   ├── RiskPanel.tsx
│   └── AuditChecklist.tsx
├── providers/               # React context providers
│   └── Web3Provider.tsx
├── config/                  # Configuration files
│   └── contracts.ts         # Contract addresses and ABIs
├── mock/                    # Mock data for demo mode
│   ├── portfolio.ts
│   ├── positions.ts
│   └── risk.ts
├── lib/                     # Utility functions
│   └── utils.ts
└── .env.example            # Environment variables template

packages/alphagenesis-analytics/  # Analytics adapter package
├── src/
│   ├── risk-analytics.ts    # VaR, CVaR, drawdown calculations
│   ├── volatility.ts        # Volatility and beta analysis
│   ├── regime-detection.ts  # Market regime classification
│   ├── types.ts             # TypeScript interfaces
│   └── index.ts             # Main exports
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/wildhash/AlphaGenesis.git
   cd AlphaGenesis
   git checkout feat/asterdex-self-driving-yield-ui
   ```

2. **Install dependencies**
   ```bash
   cd apps/yield-engine-ui
   npm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your RPC URLs and contract addresses
   ```

4. **Run development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   ```
   http://localhost:3000
   ```

### Build for Production

```bash
npm run build
npm run start
```

## 🎯 Key Features

### 1. Landing Page
- Clear pitch for the Self-Driving Yield Engine
- Explanation of the 4 Pillars (Integrate, Stack, Automate, Protect)
- Trust model highlights
- Live stats (TVL, APY, Active Strategies)

### 2. Dashboard
- User portfolio overview
- Total value, deposits, yield earned, P&L
- Active positions display
- Recent transaction history
- Deposit/Withdraw functionality

### 3. Strategy Visualization
- Visual flow diagram of the yield strategy
- Explanation of each step (Earn → Stack → Hedge)
- Stress scenario analysis
- Core principles documentation

### 4. Positions Management
- Detailed positions table
- Filter by type (Earn, LP, Farm)
- Sort by various metrics
- Individual position details
- Health indicators

### 5. Risk Analytics
- Market regime detection
- VaR and CVaR metrics
- Maximum drawdown analysis
- Protocol exposure breakdown
- Historical risk charts
- Sharpe and Sortino ratios

### 6. Documentation
- Architecture overview
- Trust model explanation
- Security checklist
- Component documentation
- External resources

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env.local` and configure:

```bash
# Chain Configuration
NEXT_PUBLIC_CHAIN_ID=56                    # BNB Mainnet
NEXT_PUBLIC_TESTNET_CHAIN_ID=97            # BNB Testnet

# RPC URLs
NEXT_PUBLIC_BNB_RPC_URL=https://bsc-dataseed.binance.org/
NEXT_PUBLIC_BNB_TESTNET_RPC_URL=https://data-seed-prebsc-1-s1.binance.org:8545/

# Contract Addresses (update when deployed)
NEXT_PUBLIC_ASTER_EARN_VAULT_ADDRESS=0x...
NEXT_PUBLIC_STACK_ROUTER_ADDRESS=0x...
NEXT_PUBLIC_STRATEGY_CONTROLLER_ADDRESS=0x...
NEXT_PUBLIC_PANCAKE_LP_MANAGER_ADDRESS=0x...

# Application Settings
NEXT_PUBLIC_ENABLE_MOCK_MODE=true
```

### Mock Mode

The UI runs in **Mock Mode** by default when contracts are not deployed. This allows:

- Full UI demonstration without live contracts
- Testing all features with realistic data
- Showcase at hackathons and demos

To disable mock mode once contracts are deployed:
1. Update contract addresses in `.env.local`
2. Set `NEXT_PUBLIC_ENABLE_MOCK_MODE=false`

## 🎨 Customization

### Theme Colors

The UI uses an emerald/green theme for BNB Chain. To customize, edit `tailwind.config.ts`:

```typescript
theme: {
  extend: {
    colors: {
      primary: colors.emerald,
      // Add custom colors here
    }
  }
}
```

### Adding New Pages

1. Create page in `app/` directory
2. Add route to `components/Header.tsx`
3. Update navigation links

## 🔐 Security & Trust Model

### Four Pillars

1. **Integrate**: AsterDEX Earn as the primary yield primitive
2. **Stack**: Composable pipeline for yield optimization
3. **Automate**: All automation is contract-governed, no manual triggers
4. **Protect**: 100% non-custodial, no admin keys

### Hard Prohibitions

❌ No server that signs transactions  
❌ No cron jobs or off-chain automation  
❌ No admin routes or privileged roles  
❌ No manual execution buttons for strategy  

✅ User-signed transactions only  
✅ Read-only RPC calls  
✅ Wallet-controlled deposits/withdrawals  

## 📊 AlphaGenesis Integration

The UI integrates with existing AlphaGenesis analytics modules through the `packages/alphagenesis-analytics` adapter:

### Adapted Modules

- **Risk Analytics**: VaR, CVaR, drawdown (from `alphagenesis/risk/var_calculator.py`)
- **Volatility**: Volatility and beta calculations (from `alphagenesis/risk/garch_model.py`)
- **Regime Detection**: Market regime classification (from `alphagenesis/features/market_regime.py`)

### Usage Example

```typescript
import { calculateVaR, detectRegime, calculateVolatility } from '@/../../packages/alphagenesis-analytics'

const returns = [0.01, -0.02, 0.015, ...]
const var95 = calculateVaR(returns, 0.95)
const regime = detectRegime(prices, volumes)
const vol = calculateVolatility(returns, 30)
```

## 🧪 Development

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler check
```

### Code Quality

The project follows strict TypeScript and ESLint rules:

```bash
npm run lint         # Check for linting issues
npm run lint:fix     # Auto-fix linting issues
```

### Testing

```bash
npm run test         # Run tests (when implemented)
npm run test:watch   # Run tests in watch mode
```

## 🚢 Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Configure environment variables
4. Deploy

### Self-Hosted

```bash
npm run build
npm run start
# Or use PM2, Docker, etc.
```

### Environment-Specific Configuration

- **Development**: Uses testnet by default
- **Production**: Configure mainnet in environment variables

## 📱 Mobile Support

The UI is fully responsive and supports:

- Mobile phones (320px+)
- Tablets (768px+)
- Desktops (1024px+)

## 🔗 Integration with Smart Contracts

When smart contracts are deployed:

1. Update contract addresses in `.env.local`
2. Add ABIs to `config/contracts.ts`
3. Implement contract interaction hooks
4. Test on testnet first
5. Deploy to mainnet

### Example Contract Hook

```typescript
import { useContractRead } from 'wagmi'
import { CONTRACTS } from '@/config/contracts'

export function useVaultBalance() {
  const { data } = useContractRead({
    address: CONTRACTS.ASTER_EARN_VAULT.address,
    abi: CONTRACTS.ASTER_EARN_VAULT.abi,
    functionName: 'balanceOf',
    args: [userAddress]
  })
  return data
}
```

## 🆘 Troubleshooting

### Common Issues

**Issue**: Wallet won't connect  
**Solution**: Make sure you're on BNB Chain (56) or testnet (97)

**Issue**: "Wrong Network" error  
**Solution**: Switch to BNB Chain in your wallet

**Issue**: Contract addresses show as 0x000...  
**Solution**: This is expected in mock mode. Update `.env.local` when contracts are deployed

**Issue**: Build fails  
**Solution**: Run `npm install` again and check Node.js version (18+ required)

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Wagmi Documentation](https://wagmi.sh)
- [RainbowKit Documentation](https://www.rainbowkit.com)
- [BNB Chain Documentation](https://docs.bnbchain.org)
- [AsterDEX Documentation](https://asterdex.com/docs)

## 🤝 Contributing

This project was built for the BNB Chain Yield Strategy Hackathon. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🏆 Hackathon Submission

This UI is part of the AsterDEX Self-Driving Yield Engine submission for the BNB Chain Yield Strategy Hackathon.

**Submission Highlights**:
- ✅ Production-grade frontend
- ✅ Fully decentralized and non-custodial
- ✅ No off-chain execution or admin keys
- ✅ Integrates existing AlphaGenesis analytics
- ✅ Clear documentation and trust model
- ✅ Ready for contract integration

---

**Built with ❤️ for the BNB Chain ecosystem**
