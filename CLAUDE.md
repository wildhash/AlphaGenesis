# Project: CryptoTradingAI - FINAL LAP SPRINT

## GCP Project Information
- **Project Name:** CryptoTradingAI
- **Project Number:** 747247574746
- **Project ID:** gemiadvan
- **Environment:** Google Cloud Platform (GCP)
- **Interface:** SSH-in-browser

## Current Status: OVERDRIVE MODE
- **Position:** 1st place
- **Phase:** Final lap sprint - bringing home the gold
- **Priority:** Peak performance optimization
- **Branch:** `claude/weex-trading-system-JjDSY`

## Critical Context for CLI Session

### System State
- **Repository:** `/home/user/AlphaGenesis` (wildhash/AlphaGenesis)
- **Working System:** AlphaGenesis - AI quantitative trading bot
- **Competition:** WEEX AI Wars Hackathon - LIVE TRADING
- **Recent Fix:** Signal stall emergency resolved (forced momentum mode)

### Last Known Performance
- In 1st place but need overdrive to secure win
- Recently recovered from 4+ hour signal stall
- System trading actively with momentum-only strategy
- Monitoring for any performance degradation

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
