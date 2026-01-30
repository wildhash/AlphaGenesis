# Claude Code Starter Prompt - AlphaGenesis Trading System

**Copy and paste this into a new Claude Code session to quickly restore context:**

---

## Quick Context

I'm working on **AlphaGenesis**, an AI-powered quantitative trading system competing in the WEEX AI Wars Hackathon. This is a real-time competition where every hour counts.

**Repository:** `/home/user/AlphaGenesis` (wildhash/AlphaGenesis)
**Active Branch:** `claude/weex-trading-system-JjDSY`
**Status:** Recently deployed emergency fix for signal stall

## Critical Background

### Recent Emergency Fix (Deployed)
The trading system had a **complete signal stall for 4+ hours** - ZERO trades placed.

**Root cause:** The contextual bandit learned that the 'flat' (no trading) strategy was better than 'momentum' because recent trades were losing money. This caused:
- Bandit selecting 'flat' → returns HOLD → no signals → complete stall
- Major competition ranking loss

**Fix deployed (commit 287c82a):**
- Forced momentum-only mode in `sdm_engine.py:157`
- Removed 'flat' from bandit strategies: `strategies=['momentum']`
- Added diagnostic logging (DIAG_SIGNAL_GENERATED, etc.)
- Created `emergency_unstall.sh` to reset bandit state

### System Architecture
- **Strategic Decision Making Engine** (`alphagenesis/features/sdm_engine.py`) - Contextual bandit + signal generation
- **Momentum Hybrid Engine** - Generates LONG/SHORT signals based on RSI + momentum
- **Regime Detection** - Classifies market conditions (HIGH/MEDIUM/LOW volatility, TRENDING/RANGING)
- **Multi-Agent System** - Arbitrage, market maker, scalper, swing trader agents
- **Risk Management** - VaR, GARCH, regime-aware position sizing
- **WEEX Exchange Integration** - REST + WebSocket for real-time trading

### Competition Context
- **8 trading symbols** on WEEX exchange
- **P&L-based ranking** - Profits determine competition placement
- **Recent performance:** Working to close $144 gap, recovering from $40 loss
- **Urgency:** Every minute of downtime = ranking loss

## What You Need to Know

### Key Files
- `alphagenesis/features/sdm_engine.py` - ⭐ Core engine (bandit, regime, signals)
- `alphagenesis/features/momentum_hybrid_engine.py` - Signal generation logic
- `SIGNAL_STALL_FIX.md` - Comprehensive emergency fix documentation
- `CLAUDE_CONTEXT_MEMORY.md` - Full detailed context (read this for deep dive)

### State Files (in `/tmp/`)
- `bandit_state.json` - Bandit learned preferences (reset to fix stall)
- `position_ledger.json` - Current positions
- `trading_journal.db` - Decision history

### Git Workflow (CRITICAL)
- **ALWAYS** work on branch: `claude/weex-trading-system-JjDSY`
- **ALWAYS** push with: `git push -u origin claude/weex-trading-system-JjDSY`
- Branch MUST start with `claude/` or push fails (403)
- Retry network errors up to 4 times with exponential backoff (2s, 4s, 8s, 16s)

### Monitoring Commands
```bash
# Check if signals are generating (CRITICAL after fix)
sudo journalctl -u sdm-trading.service -o cat -f | \
  egrep -i 'DIAG_SIGNAL_GENERATED|Placing order|WEEX_ORDER_RESPONSE' \
  --line-buffered --color=always

# Count signals in last 30 minutes
sudo journalctl -u sdm-trading.service -o cat --since "30 minutes ago" | \
  grep "DIAG_SIGNAL_GENERATED" | wc -l

# Check for errors
sudo journalctl -u sdm-trading.service -o cat --since "15 minutes ago" | \
  grep -i "error\|exception" | tail -20
```

## Current Task (Update this based on actual request)

**Default action if no specific task:** Check post-deployment status
1. Verify signals are generating (look for DIAG_SIGNAL_GENERATED in logs)
2. Confirm orders are being placed (WEEX_ORDER_RESPONSE logs)
3. Monitor for any errors
4. Report status of signal generation recovery

## Immediate Actions for New Session

Please:
1. **Read** `CLAUDE_CONTEXT_MEMORY.md` if you need comprehensive background
2. **Check** current git status: `git status` and `git log -5 --oneline`
3. **Ask** me what I need help with today

Then proceed based on my request. Common tasks include:
- Monitoring post-deployment status
- Investigating performance issues
- Optimizing strategy parameters
- Fixing new bugs or errors
- Improving competition performance

## Key Constraints

- **Competition urgency** - Deploy fast, iterate quickly
- **No overthinking** - Simple fixes > perfect solutions when racing
- **Diagnostic logging** - Always add logs for debugging
- **Test carefully** - But don't block deployment for perfect tests
- **Document critical changes** - Update .md files for deployment guides

## Recent Commits (Last 5)
```
718b784 DOCS: Add comprehensive signal stall fix deployment guide
287c82a EMERGENCY: Fix complete signal stall - bandit learned flat > momentum
41f1eb5 TOOLS: Add Codex verification protocol for regime-aware sizing deployment
c304643 COMPETE: Regime-aware position sizing to close $144 gap
227e2e0 OPTIMIZE: Aggressive competition settings to recover from $40 loss
```

Pattern: Rapid iteration for competition recovery

---

## Example Opening Messages

**For status check:**
> "Please check the deployment status of the signal stall fix. Are signals being generated? Monitor the logs for DIAG_SIGNAL_GENERATED and report what you find."

**For performance issue:**
> "The system is generating signals but we're still losing money. Please analyze the recent trades and identify why the momentum strategy is underperforming."

**For new feature:**
> "We need to implement regime-aware stop losses that widen in high volatility and tighten in low volatility. Read the current stop loss logic and propose changes."

**For emergency:**
> "The system stopped trading again. Please investigate the logs immediately and diagnose the issue. Check for errors, signal generation, and bandit state."

---

**END OF STARTER PROMPT**

For full context, read: `/home/user/AlphaGenesis/CLAUDE_CONTEXT_MEMORY.md`
