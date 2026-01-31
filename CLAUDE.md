# Project: CryptoTradingAI - FINAL LAP SPRINT

## GCP Project Information
- **Project Name:** CryptoTradingAI
- **Project Number:** 747247574746
- **Project ID:** gemiadvan
- **Environment:** Google Cloud Platform (GCP)
- **Interface:** SSH-in-browser

## Current Status: COMEBACK MODE
- **Position:** 2nd place (fell from 1st)
- **Phase:** Critical recovery - reclaim 1st place
- **Priority:** LOW_VOL override verification + threshold tuning
- **Branch:** `claude/weex-trading-system-JjDSY`
- **Issue:** SSH resource crash (single session only)

## Critical Context for CLI Session

### System State
- **Dev Repository:** `/home/user/AlphaGenesis` (wildhash/AlphaGenesis)
- **Production Path:** `/opt/AlphaGenesis` (live trading system on GCP)
- **Working System:** AlphaGenesis - AI quantitative trading bot
- **Competition:** WEEX AI Wars Hackathon - LIVE TRADING
- **Recent Deployments:**
  1. Signal stall fix: Forced momentum-only mode (strategies=['momentum'])
  2. LOW_VOL override: Force momentum in LOW_VOLATILITY regime (just deployed)

### Last Known Performance
- **Current:** 2nd place (fell from 1st during signal analysis)
- **Cause:** Likely LOW_VOL regime blocking signals (override just deployed)
- Recently recovered from 4+ hour signal stall
- System now has LOW_VOL override forcing momentum strategy
- **Critical:** Verify override working + tune LOW_VOL thresholds
- **SSH Warning:** VM resource constrained - single session only (2nd SSH crashed)

### Key Files to Know
- `alphagenesis/features/sdm_engine.py` - Core trading engine (bandit + signals)
- `alphagenesis/features/momentum_hybrid_engine.py` - Signal generation
- `CLAUDE_CONTEXT_MEMORY.md` - Full detailed context
- `CLAUDE_STARTER_PROMPT.md` - Quick context restore

### State Files (Production)
- `/tmp/bandit_state.json` - Strategy learning state
- `/tmp/position_ledger.json` - Active positions
- `/tmp/trading_journal.db` - Trade history

### Production Service
- **Service:** `sdm-trading.service` (systemd)
- **Logs:** `sudo journalctl -u sdm-trading.service -o cat -f`
- **Status:** `sudo systemctl status sdm-trading.service`

### Quick Health Check
```bash
# Signal generation (should see activity)
sudo journalctl -u sdm-trading.service -o cat --since "5 minutes ago" | grep "DIAG_SIGNAL_GENERATED" | wc -l

# Recent errors
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | grep -i "error\|exception" | tail -10

# Account status
python3 scripts/check_weex_account.py
```

### Git Workflow (CRITICAL)
- **Branch:** ALWAYS use `claude/weex-trading-system-JjDSY`
- **Push:** `git push -u origin claude/weex-trading-system-JjDSY`
- **Retry:** Up to 4 times with backoff (2s, 4s, 8s, 16s) on network errors
- **Naming:** MUST start with `claude/` or push fails (403)

## Current Mission: FINAL SPRINT OPTIMIZATION

**Objectives:**
1. Monitor system performance in real-time
2. Identify and eliminate any performance bottlenecks
3. Optimize trading parameters for maximum P&L
4. Ensure zero downtime during final competition hours
5. Secure 1st place with aggressive but controlled trading

**Watch For:**
- Signal generation rate drops
- Order execution delays
- Strategy selection anomalies
- Risk management being too conservative
- Any error patterns in logs

## Quick Start for CLI

```bash
# 1. Check system health
sudo systemctl status sdm-trading.service

# 2. Monitor live signals
sudo journalctl -u sdm-trading.service -o cat -f | egrep 'DIAG_SIGNAL_GENERATED|Placing order|WEEX_ORDER_RESPONSE' --line-buffered --color=always

# 3. Check recent performance
python3 scripts/check_weex_account.py

# 4. Ready to optimize based on findings
```

## Competition Context
- **Trading Symbols:** 8 crypto pairs on WEEX
- **Ranking:** P&L-based (profit determines winner)
- **Time Pressure:** Every minute counts in final sprint
- **Strategy:** Momentum-only (flat removed after stall incident)

---

**For comprehensive context, read:** `CLAUDE_CONTEXT_MEMORY.md`
**For quick restore, use:** `CLAUDE_STARTER_PROMPT.md`

**LET'S WIN THIS.**
