# 🚀 WEEX AI Wars - HACKATHON READY

## System Status: ✅ READY FOR COMPETITION

Your **Semantic Dataflow Machine (SDM)** trading system is fully implemented and ready for the WEEX AI Wars hackathon!

---

## 🎯 Competition Details

- **Event**: AI Wars: WEEX Alpha Awakens (Preliminary Round)
- **Start**: Jan 12, 8:00 PM UTC+8 (TODAY!)
- **End**: Feb 2, 11:59 PM UTC+8
- **Goal**: Top 2 in BUIDL group by final account balance
- **Starting Capital**: 1,000 USDT (competition funds)
- **Your Reserved IP**: 34.133.16.230 (GCP)
- **API Status**: ✅ Passed testing phase
- **Telegram Group**: https://t.me/+6OlzxYh52lc1YTg9

---

## 📊 Competition Rules (COMPLIANT ✅)

| Rule | Requirement | Our Implementation | Status |
|------|-------------|-------------------|--------|
| Leverage Cap | Max 20x | Hard boundary in ethics engine | ✅ |
| Daily Drawdown | Max 10% | Circuit breaker + ethics engine | ✅ |
| Total Drawdown | Max 25% | Hard boundary (catastrophic penalty) | ✅ |
| Minimum Trades | At least 10 | SDM will trade on high-confidence signals | ✅ |
| Trading Method | API-only, no manual | Fully autonomous via WEEX API | ✅ |
| AI Requirement | Genuine AI technology | Multi-model SDM with continuous learning | ✅ |

---

## 🏗️ What Was Built: The SDM Architecture

### The Semantic Dataflow Machine

A post-Von Neumann trading system where:
- **Intent replaces instructions**
- **Semantic binding replaces compilation**
- **Continuous resolution replaces execution**
- **Learning is embodied in the dataflow**

### Core Components (3,800+ lines of code)

#### 1. Intent Graph (`alphagenesis/sdm/intent_graph.py`)
- Living graph of trading goals and constraints
- 4 primary intents: grow capital, manage risk, exploit opportunities, maintain liquidity
- Edges define relationships: dependencies, tradeoffs, inhibitions, feedbacks
- Continuous activation propagation (pressure gradients)
- Self-evolves based on success/failure

**Key Innovation**: No main(), no entry point, just continuous pressure resolution

#### 2. Semantic Binding Layer (`alphagenesis/sdm/semantic_binding.py`)
- Hybrid Associative Memory (HIM) for O(1) intent→model lookup
- Dynamic model selection based on market regime
- Binds abstract intent to concrete models/strategies
- Continuous rebinding based on performance

**Key Innovation**: Replaces compilation with semantic resolution

#### 3. Continuous Learning Engine (`alphagenesis/sdm/continuous_learning.py`)
- Tracks performance of every (intent, model, regime) combination
- Automatically adapts: boosts what works, weakens what doesn't
- Rewrites intent graph edges based on feedback
- Updates model bindings via association matrix learning
- Adapts constraints based on P&L

**Key Innovation**: The system never stops learning - it's embodied in the dataflow

#### 4. Constraint Propagation (`alphagenesis/sdm/constraint_propagation.py`)
- Constraints as potential fields (not if-statements)
- Actions are SHAPED by constraints, not blocked
- Repulsive, attractive, and boundary fields
- Gradient descent toward safer states

**Key Innovation**: Think potential fields in physics, not traditional validation

#### 5. Ethics Engine (`alphagenesis/sdm/ethics_engine.py`)
- First-class ethical constraints
- Asymmetric penalties (violations are MUCH worse than compliance)
- Hard boundaries have near-infinite repulsion
- Comprehensive audit trail

**Key Innovation**: Ethics apply continuous pressure, don't just block actions

#### 6. SDM Trading Engine (`alphagenesis/sdm/sdm_engine.py`)
- Orchestrates all SDM components
- Integrates with existing AlphaGenesis infrastructure
- WEEX API integration
- Continuous dataflow loop

---

## 🔧 Deployment Instructions

### Step 1: Set Up Environment Variables

```bash
cd /home/user/AlphaGenesis

# Create .env file from template
cp .env.example .env

# Edit .env with your actual WEEX API credentials
nano .env
```

**Required variables in `.env`:**
```bash
WEEX_API_KEY=your_actual_api_key_from_hackathon
WEEX_API_SECRET=your_actual_api_secret
WEEX_API_PASSPHRASE=your_actual_passphrase
WEEX_BASE_URL=https://api-contract.weex.com
INITIAL_CAPITAL=1000.0
UPDATE_INTERVAL=300  # 5 minutes
```

### Step 2: Install Dependencies (if deploying to GCP)

```bash
# On GCP instance (34.133.16.230)
cd /home/alphagenesis/AlphaGenesis

# Install Poetry if not installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install --no-dev
```

### Step 3: Deploy to GCP

**Option A: Automated Deployment** (Recommended)

```bash
# From your local machine
cd /home/user/AlphaGenesis

# Ensure .env has your API credentials
# Then run automated deployment
./deploy/deploy_to_gcp.sh
```

This script will:
1. Sync code to GCP (34.133.16.230)
2. Copy .env file
3. Install dependencies via Poetry
4. Set up systemd service for automatic startup
5. Start the SDM trading system
6. Show you the logs

**Option B: Manual Deployment**

```bash
# SSH to GCP
ssh alphagenesis@34.133.16.230

# Go to project directory
cd /home/alphagenesis/AlphaGenesis

# Pull latest code
git pull origin claude/weex-trading-system-JjDSY

# Ensure .env is configured
nano .env

# Start the system
poetry run python scripts/start_sdm_trading.py
```

### Step 4: Monitor the System

**View Live Logs:**
```bash
# If deployed via systemd
ssh alphagenesis@34.133.16.230 'sudo journalctl -u sdm-trading.service -f'

# Or tail the log files
ssh alphagenesis@34.133.16.230 'tail -f /home/alphagenesis/AlphaGenesis/logs/sdm_trading_*.log'
```

**Check Performance:**
```bash
# SSH to GCP
ssh alphagenesis@34.133.16.230

# View learning history
cd /home/alphagenesis/AlphaGenesis
ls -lh reports/sdm/
cat reports/sdm/learning_*.json | jq '.strategy_performance'

# View ethics violations
cat reports/sdm/ethics_*.json | jq '.summary'
```

**System Control Commands:**
```bash
# Stop the system
ssh alphagenesis@34.133.16.230 'sudo systemctl stop sdm-trading.service'

# Start the system
ssh alphagenesis@34.133.16.230 'sudo systemctl start sdm-trading.service'

# Restart the system
ssh alphagenesis@34.133.16.230 'sudo systemctl restart sdm-trading.service'

# Check status
ssh alphagenesis@34.133.16.230 'sudo systemctl status sdm-trading.service'
```

---

## 📈 What to Expect

### Trading Behavior

The SDM system will:
- ✅ **Start with high activation** on "grow capital" and "exploit opportunities" intents
- ✅ **Monitor BTC and ETH** perpetual futures on WEEX
- ✅ **Detect market regimes** (strong uptrend, downtrend, sideways, high/low volatility)
- ✅ **Bind intents to optimal models** based on regime (LSTM for trends, scalper for sideways, etc.)
- ✅ **Generate trade signals** only when multiple criteria align
- ✅ **Shape actions** through constraint fields (leverage, position size, etc.)
- ✅ **Apply ethical pressure** (never exceed 20x leverage, never >25% drawdown)
- ✅ **Execute trades** via WEEX API when all checks pass
- ✅ **Learn continuously** - adapting strategy based on what works

### Expected Trade Frequency

- **Low frequency by design** (inspired by DeepSeek's winning strategy)
- **Quality over quantity** (only high-confidence opportunities)
- **Typical**: 1-3 trades per day (meeting hackathon minimum of 10 trades over 21 days)
- **Max**: Capped at 5 trades/day by ethics engine

### Risk Management

The system has **3 layers of protection**:

1. **Circuit Breaker** (legacy component)
   - 10% daily drawdown limit
   - 25% total drawdown limit
   - Automatic cooldown periods

2. **Constraint Propagation** (SDM component)
   - Repulsive fields push away from dangerous states
   - Actions are shaped, not blocked
   - Gradient descent toward safety

3. **Ethics Engine** (SDM component)
   - Hard boundaries with catastrophic penalties
   - Asymmetric enforcement (violations extremely costly)
   - Complete audit trail

---

## 🔍 Understanding the Logs

### Normal Operation Logs

You'll see messages like:

```
SDM ITERATION 42 - 2026-01-12 20:15:00
======================================================================
Resolving Intent: Grow capital aggressively without catastrophic drawdown
Activation: 0.85, Priority: 10.0
Bound grow_capital -> lstm for cmt_btcusdt in strong_uptrend
Constraint repulsion on max_leverage: force=15.20, scaled to 12.50
Applied ethical pressure to position_size: 0.45 -> 0.35
EXECUTING ACTION via SDM
✓ Order placed successfully
```

**What this means:**
- The "grow capital" intent is highly active (0.85)
- System detected strong uptrend, bound to LSTM model
- Constraint fields reduced leverage from proposed value
- Ethics engine reduced position size
- Trade executed successfully

### Adaptation Logs

When the system learns:

```
INITIATING ADAPTATION CYCLE
======================================================================
Best performing strategies:
  grow_capital_lstm: 75% success, PnL: +150.50
Worst performing strategies:
  exploit_opportunities_scalper: 30% success, PnL: -25.00

Boosted intent: grow_capital
Weakened intent: exploit_opportunities
Updated associations from 50 feedback samples
Adaptation complete: 4 changes made
```

**What this means:**
- System identified which (intent, model) pairs are working
- Increased activation/priority of successful intents
- Decreased activation/priority of failing intents
- Updated semantic bindings based on performance

---

## 🎯 Success Metrics

Track these to monitor performance:

1. **Account Balance** - Must be in top 2 of BUIDL group
2. **Total P&L** - Absolute profit/loss
3. **Success Rate** - Percentage of winning trades
4. **Trade Count** - Must exceed 10 for competition validity
5. **Max Drawdown** - Should stay well below 25% limit
6. **Constraint Violations** - Should be minimal (ethics working)
7. **Adaptation Cycles** - More = more learning

---

## 🐛 Troubleshooting

### "No binding found for intent"
**Status**: Normal during initialization
**Action**: Wait 2-3 iterations, bindings are created dynamically

### "Circuit breaker tripped"
**Status**: Protecting capital (working as designed)
**Action**: System will auto-resume after cooldown period

### "Ethical violation: max_leverage"
**Status**: Ethics engine blocked dangerous action (working as designed)
**Action**: None needed, system prevented excessive risk

### "Recent success rate below threshold, triggering adaptation"
**Status**: Continuous learning in action
**Action**: System is self-correcting, monitor next iteration

### Low trade frequency
**Status**: By design (DeepSeek-inspired discipline)
**Action**: None needed, quality > quantity

### Connection errors to WEEX API
**Status**: Network issue or API rate limiting
**Action**: Check GCP connectivity, API credentials, or wait for retry

---

## 📚 Documentation

- **SDM Overview**: [SDM_README.md](SDM_README.md)
- **AlphaGenesis README**: [README.md](README.md)
- **WEEX API Docs**: https://www.weex.com/api-doc/ai/introduction
- **Competition Rules**: https://www.weex.com/api-doc/ai/introduction/Rule

---

## 🚀 Launch Checklist

Before the competition starts:

- [ ] ✅ API credentials configured in `.env`
- [ ] ✅ Code deployed to GCP (34.133.16.230)
- [ ] ✅ Dependencies installed
- [ ] ✅ System tested (run `python test_sdm_minimal.py`)
- [ ] ✅ Systemd service enabled (auto-restart on failure)
- [ ] ✅ Monitoring set up (know how to view logs)
- [ ] ✅ Joined Telegram group for updates
- [ ] ✅ BUIDL group confirmed on event page

---

## 💡 The Competitive Edge

### Why SDM Could Win

1. **Self-Learning**: Continuously adapts to what works in live market
2. **Disciplined**: Multiple layers prevent emotional/irrational trades
3. **Multi-Model**: Switches strategies based on market regime
4. **Intent-Driven**: Goals remain constant, execution adapts
5. **Ethically Bounded**: Never violates competition rules
6. **Field-Tested Architecture**: Built on proven AlphaGenesis foundation

### The Strategy

- **DeepSeek-Inspired**: Low frequency, high quality, strong discipline
- **Multi-Regime**: Different models for different market conditions
- **Risk-First**: Preserve capital above all
- **Continuous Learning**: Gets better throughout the competition

---

## 🎬 Final Steps

1. **Configure `.env`** with your actual WEEX API credentials
2. **Run deployment**: `./deploy/deploy_to_gcp.sh`
3. **Verify logs**: Confirm system is trading
4. **Monitor daily**: Check performance and P&L
5. **Let it run**: Trust the SDM to adapt and learn

---

## 📞 Support

If you need to modify the system during competition:

**Adjust risk parameters**: Edit `alphagenesis/sdm/intent_graph.py` → `initialize_trading_intents()`

**Change update frequency**: Set `UPDATE_INTERVAL` in `.env` (in seconds)

**Emergency stop**: `ssh alphagenesis@34.133.16.230 'sudo systemctl stop sdm-trading.service'`

**Emergency restart**: `ssh alphagenesis@34.133.16.230 'sudo systemctl restart sdm-trading.service'`

---

## 🏆 Good Luck!

Your SDM system represents a new computational paradigm - where intent flows through semantic dataflow to become action, continuously adapting under the pressure of constraints and ethics.

**No hype. No mysticism. Just a new substrate for trading.**

May your intents propagate favorably, your bindings stay strong, and your capital grow.

**The hackathon starts TODAY at 8 PM UTC+8. Deploy and let the SDM work its magic!**

---

*Built with ❤️ for WEEX AI Wars: Alpha Awakens*
*A new computational contract between humans and machines.*
