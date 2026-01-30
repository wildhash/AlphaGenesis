# Claude Code Context Memory - AlphaGenesis Trading System

**Last Updated:** 2026-01-30
**Session Branch:** `claude/weex-trading-system-JjDSY`
**Status:** EMERGENCY FIX DEPLOYED - Signal stall resolved

---

## Project Overview

**AlphaGenesis** is an institutional-grade, AI-powered quantitative trading system built for the WEEX AI Wars Hackathon. It's a competition-focused algorithmic trading platform that combines machine learning, contextual bandits, and sophisticated risk management to trade crypto on the WEEX exchange.

**Repository:** wildhash/AlphaGenesis
**Working Directory:** `/home/user/AlphaGenesis`
**Main Branch:** (not specified - use branch above for all work)
**Development Branch:** `claude/weex-trading-system-JjDSY`

---

## Critical Recent Work - Signal Stall Emergency Fix

### The Crisis (Resolved)
**Timeline:** 4+ hours of ZERO trading signals
- No orders placed
- No DIAG_ACTION logs
- Only heartbeat logs present
- **Impact:** Significant competition ranking loss

### Root Cause Discovered
The **Contextual Bandit learned that 'flat' (no trading) was better than 'momentum' strategy**:

1. **Bandit Architecture** (`alphagenesis/features/sdm_engine.py:156-162`)
   - Strategies: `['momentum', 'flat']`
   - Algorithm: Upper Confidence Bound (UCB)
   - Learning from trade rewards over time

2. **What Happened:**
   - Recent momentum trades lost money
   - Bandit calculated: `mean_reward('flat')` = 0.0 > `mean_reward('momentum')` (negative)
   - Bandit kept selecting 'flat' strategy
   - 'flat' returns HOLD → no signals → complete stall

3. **Signal Generation Flow:**
   ```python
   chosen_strategy = self.bandit.select_strategy(symbol, regime_str)
   if chosen_strategy == 'flat':
       return {'direction': 'HOLD', 'confidence': 0.0, 'strategy': 'flat'}
   ```

### Fix Deployed (Commit: 287c82a)
1. **Forced momentum-only mode** - Removed 'flat' from bandit strategies
2. **Added diagnostic logging** - DIAG_STRATEGY_SELECT, DIAG_SIGNAL_GENERATED, etc.
3. **Created emergency_unstall.sh** - Resets bandit state and restarts service
4. **Documentation** - Comprehensive deployment guide in SIGNAL_STALL_FIX.md

**File Changed:** `alphagenesis/features/sdm_engine.py:157`
```python
# Before: strategies=['momentum', 'flat']
# After:  strategies=['momentum']  # FORCE MOMENTUM ONLY
```

---

## System Architecture

### Core Components

1. **Multi-Agent Trading System** (`alphagenesis/agents/`)
   - Arbitrage Agent
   - Market Maker Agent
   - Scalper Agent
   - Swing Trader Agent
   - Multi-agent coordinator

2. **Strategic Decision Making Engine** (`alphagenesis/features/sdm_engine.py`)
   - **Contextual Bandit** (UCB algorithm) - Strategy selection
   - **Regime Detection** - Market condition classification
   - **Intent Graph** - Action validation
   - **Position Ledger** - State tracking
   - **Momentum Hybrid Engine** - Signal generation

3. **Data Pipeline** (`alphagenesis/data/`)
   - WEEX Exchange client (REST + WebSocket)
   - Data fetcher & storage
   - Real-time market data streaming

4. **Risk Management** (`alphagenesis/risk/`)
   - VaR Calculator
   - GARCH volatility modeling
   - Portfolio optimizer
   - Position sizing (recently updated to regime-aware)

5. **AI Reasoning** (`alphagenesis/ai/`)
   - DeepSeek Reasoner integration
   - Trade analysis and decision support

6. **Execution** (`alphagenesis/execution/`)
   - Order executor
   - Order manager
   - WEEX API integration

### Key State Files (Location: `/tmp/`)
- `bandit_state.json` - Bandit learned preferences per context
- `position_ledger.json` - Current positions and state
- `trading_journal.db` - Decision history

---

## Recent Commit History

```
718b784 DOCS: Add comprehensive signal stall fix deployment guide
287c82a EMERGENCY: Fix complete signal stall - bandit learned flat > momentum
41f1eb5 TOOLS: Add Codex verification protocol for regime-aware sizing deployment
c304643 COMPETE: Regime-aware position sizing to close $144 gap
227e2e0 OPTIMIZE: Aggressive competition settings to recover from $40 loss
44f8835 IGNORE: Add reports directory to .gitignore
4fd4ccc FIX: Remove explicit Keras dependency to resolve TensorFlow conflict
2532220 TOOLS: Add quick fix script for VM deployment
3959fb1 FIX: Migrate from deprecated Gym to Gymnasium and fix dependency issues
a219c8a DOCS: Add integration plan for Codex trade logger work
```

**Pattern:** Rapid iteration for competition recovery - fixing stalls, optimizing sizing, competitive adjustments

---

## Competition Context - WEEX AI Wars Hackathon

**Critical Constraints:**
- **Real-time competition** - Every hour of downtime = ranking loss
- **P&L driven** - Profit & Loss determines ranking
- **Multi-bot competition** - Other teams actively trading
- **8 Trading Symbols** - Must manage portfolio across multiple pairs

**Recent Performance Metrics:**
- $144 gap to close (from commit c304643)
- $40 loss recovery effort (from commit 227e2e0)
- Signal stall caused 4+ hours of zero activity
- Competition urgency = deploy fast, optimize iteratively

**Trading Pairs:** (Inferred from multi-symbol system)
- BTC/USDT, ETH/USDT, and 6 others (check config for exact list)

---

## Key Technical Concepts

### 1. Contextual Bandit
- **Location:** `sdm_engine.py`
- **Purpose:** Learn which strategy (momentum/flat) works best per context
- **Context:** (symbol, regime) tuple
- **Algorithm:** Upper Confidence Bound (UCB)
- **State:** Persisted in `/tmp/bandit_state.json`

### 2. Regime Detection
- **Types:** HIGH_VOLATILITY, MEDIUM_VOLATILITY, LOW_VOLATILITY, TRENDING, RANGING
- **Purpose:** Classify market conditions
- **Usage:** Influences position sizing and strategy selection

### 3. Momentum Hybrid Engine
- **Location:** `alphagenesis/features/momentum_hybrid_engine.py`
- **Signals:** LONG (RSI > 55, momentum > 1.0%), SHORT (RSI < 45, momentum < -1.0%)
- **Current Thresholds:** May be too strict if generating zero signals

### 4. Position Sizing
- **Recent Update:** Regime-aware sizing (commit c304643)
- **Purpose:** Adjust position size based on market conditions
- **Impact:** Larger positions in favorable regimes

### 5. Intent Graph
- **Purpose:** Validate proposed actions against constraints
- **Risk:** Can reject all actions if constraints too strict

---

## Deployment & Monitoring

### Production Environment
- **Service:** `sdm-trading.service` (systemd)
- **Logs:** `sudo journalctl -u sdm-trading.service -o cat -f`
- **Config:** `config/config.yaml` + `.env` file
- **WEEX API:** Requires API key/secret in environment

### Key Monitoring Commands

**Signal Generation (Real-time):**
```bash
sudo journalctl -u sdm-trading.service -o cat -f | \
  egrep -i 'DIAG_STRATEGY_SELECT|DIAG_SIGNAL_GENERATED|Placing order|WEEX_ORDER_RESPONSE' \
  --line-buffered --color=always
```

**Signal Count (Last 30 min):**
```bash
sudo journalctl -u sdm-trading.service -o cat --since "30 minutes ago" | \
  grep "DIAG_SIGNAL_GENERATED" | wc -l
```

**Error Check:**
```bash
sudo journalctl -u sdm-trading.service -o cat --since "15 minutes ago" | \
  grep -i "error\|exception\|failed" | tail -20
```

### Emergency Scripts
- `emergency_unstall.sh` - Reset bandit state, restart service
- `check_production_status.sh` - Production health check
- `analyze_logs.sh` - Log analysis
- `check_weex_account.py` - Account status
- `close_all_positions.py` - Emergency position closure

---

## Known Issues & Next Steps

### Immediate Priorities (Post Signal Stall Fix)
1. **Monitor signal generation** - Ensure DIAG_SIGNAL_GENERATED logs appear within 5-10 minutes
2. **Verify order execution** - Check for WEEX_ORDER_RESPONSE logs
3. **Track P&L recovery** - Competition ranking dependent on profits

### Potential Follow-up Issues
1. **If signals still zero after fix:**
   - Momentum thresholds too strict (lower from 1.0% to 0.5%)
   - Market data feed issue
   - Intent graph blocking all actions

2. **If signals present but losing money:**
   - Review stop-loss widths (may be too tight)
   - Review momentum thresholds (catching false breakouts)
   - Review regime detection accuracy
   - Review position sizing (recently increased)

### Technical Debt
- Dependency migration (Gym → Gymnasium)
- TensorFlow/Keras conflicts resolved
- Multiple documentation files need consolidation

---

## File Structure Overview

```
AlphaGenesis/
├── alphagenesis/                    # Main package
│   ├── agents/                      # Multi-agent trading system
│   ├── ai/                          # DeepSeek reasoner
│   ├── arbitrage/                   # Cross-exchange arbitrage
│   ├── backtest/                    # Backtesting engine
│   ├── data/                        # WEEX client & data pipeline
│   ├── execution/                   # Order execution
│   ├── features/                    # Feature engineering & SDM engine
│   │   ├── sdm_engine.py           # ⭐ Critical: Bandit + signal generation
│   │   └── momentum_hybrid_engine.py # Signal generation logic
│   ├── models/                      # ML models (LSTM, Transformer, RL)
│   ├── risk/                        # Risk management
│   └── utils/                       # Utilities
├── config/                          # Configuration files
├── deploy/                          # Deployment scripts
├── scripts/                         # Utility scripts
├── tests/                           # Test suite
├── *.sh                            # Emergency & monitoring scripts
└── *.md                            # Documentation (MANY files)
```

---

## Git Workflow Requirements

**CRITICAL GIT RULES:**

1. **Branch:** ALWAYS work on `claude/weex-trading-system-JjDSY`
2. **Push format:** `git push -u origin claude/weex-trading-system-JjDSY`
3. **Branch naming:** MUST start with `claude/` and end with session ID or push will fail (403)
4. **Network retry:** Retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s)
5. **Fetch specific:** `git fetch origin claude/weex-trading-system-JjDSY`

**Example push with retry:**
```bash
git push -u origin claude/weex-trading-system-JjDSY || \
  (sleep 2 && git push -u origin claude/weex-trading-system-JjDSY) || \
  (sleep 4 && git push -u origin claude/weex-trading-system-JjDSY) || \
  (sleep 8 && git push -u origin claude/weex-trading-system-JjDSY)
```

---

## Communication with Codex (Human User)

**Context:** Multiple documentation files suggest collaboration with "Codex"
- `CODEX_PROMPT.md` - Integration instructions
- `FOR_CODEX_INTEGRATION_PLAN.md` - Handoff plan
- `SHARE_WITH_CODEX.md` - Status sharing
- `STATUS_FOR_CODEX.md` - Status updates
- `codex_quickstart.sh` - Quick start script

**Implication:** This is a collaborative development environment where:
- Claude Code implements fixes/features
- Codex (likely the developer) deploys to production
- Tight feedback loop for competition iteration

---

## Environment Details

- **Platform:** Linux 4.4.0
- **Working Directory:** `/home/user/AlphaGenesis`
- **Git Status:** Clean (as of session start)
- **Python:** 3.9+ (Poetry managed)
- **Key Dependencies:** TensorFlow, Gymnasium, TA-Lib, various ML libraries

---

## What to Do Next Session

### Immediate Actions
1. **Check deployment status** - Did emergency_unstall.sh work?
2. **Monitor signals** - Are DIAG_SIGNAL_GENERATED logs appearing?
3. **Verify orders** - Are orders being placed on WEEX?
4. **Track P&L** - Is system recovering from stall?

### If Signals Still Stalled
1. Read `alphagenesis/features/momentum_hybrid_engine.py` - Check thresholds
2. Check logs for DIAG_NO_SIGNAL - Momentum engine failing
3. Investigate regime detection - Is it classifying correctly?
4. Review intent graph - Is it blocking all actions?

### If Signals Present but Losing
1. Analyze stop-loss hit rate
2. Review momentum threshold effectiveness
3. Check position sizing logic
4. Analyze regime detection accuracy

### Competition Optimization
1. Close the $144 gap (if still present)
2. Optimize strategy selection
3. Improve signal quality over quantity
4. Balance risk vs. reward for competition ranking

---

## Quick Reference Commands

### Service Management
```bash
sudo systemctl status sdm-trading.service
sudo systemctl restart sdm-trading.service
sudo systemctl stop sdm-trading.service
```

### Log Monitoring
```bash
# Real-time logs
sudo journalctl -u sdm-trading.service -o cat -f

# Signal monitoring
sudo journalctl -u sdm-trading.service -o cat -f | grep "DIAG_SIGNAL_GENERATED"

# Error tracking
sudo journalctl -u sdm-trading.service -o cat --since "1 hour ago" | grep -i error
```

### State Management
```bash
# Bandit state
cat /tmp/bandit_state.json | jq

# Position ledger
cat /tmp/position_ledger.json | jq

# Reset bandit (emergency)
./emergency_unstall.sh
```

### Account Status
```bash
./check_weex_account.py
./check_production_status.sh
```

---

## Key Lessons Learned

1. **Contextual bandits can learn to avoid trading** - Need to carefully curate strategy options
2. **Competition pressure requires aggressive fixes** - Can't wait for perfect solutions
3. **Diagnostic logging is critical** - Added DIAG_* logs were essential for debugging
4. **State files matter** - `/tmp/bandit_state.json` stored the problematic learned behavior
5. **Multiple experts can be wrong** - Original diagnosis (LOW_VOLATILITY gate) was incorrect

---

**END OF CONTEXT MEMORY**

This file serves as a comprehensive knowledge base for future Claude Code sessions working on AlphaGenesis. Update this file as the project evolves.
