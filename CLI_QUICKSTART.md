# CLI QUICKSTART - FINAL LAP SPRINT

**READ THIS FIRST** - Optimized for instant context load

## THE MISSION
You're running AlphaGenesis, an AI trading bot in the WEEX AI Wars Hackathon.
**Status:** 2nd place - COMEBACK TO RECLAIM 1ST
**Location:** GCP (Project ID: gemiadvan) - SSH session (SINGLE SESSION ONLY - VM resource limited)
**Branch:** `claude/weex-trading-system-JjDSY` (ALWAYS)
**Production Path:** `/opt/AlphaGenesis` (live system)

## CRITICAL FILES (Read these if you need deep context)
- `CLAUDE.md` - GCP connection + sprint objectives (1 min read)
- `CLAUDE_STARTER_PROMPT.md` - Quick restore guide (2 min read)
- `CLAUDE_CONTEXT_MEMORY.md` - Full context (5 min read)

## RECENT HISTORY
- Fixed 4hr signal stall (bandit learned to stop trading)
- Forced momentum-only mode in `sdm_engine.py:157` (strategies=['momentum'])
- **NEW:** Applied LOW_VOL override in production `/opt/AlphaGenesis`
- Fell from 1st to 2nd place during analysis
- **Critical:** Verify LOW_VOL override working + tune thresholds

## INSTANT HEALTH CHECK
```bash
# Are we trading? (Should see signals in last 5 min)
sudo journalctl -u sdm-trading.service -o cat --since "5 minutes ago" | grep "DIAG_SIGNAL_GENERATED" | wc -l

# Any errors?
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | grep -i error | tail -5

# Account P&L
python3 scripts/check_weex_account.py
```

## LIVE MONITORING
```bash
# Watch signals + orders in real-time
sudo journalctl -u sdm-trading.service -o cat -f | egrep 'DIAG_SIGNAL_GENERATED|Placing order|WEEX_ORDER_RESPONSE' --line-buffered --color=always
```

## GIT WORKFLOW
```bash
# Commit changes
git add . && git commit -m "OPTIMIZE: [description]"

# Push (with retry on network errors)
git push -u origin claude/weex-trading-system-JjDSY || sleep 2 && git push -u origin claude/weex-trading-system-JjDSY
```

## KEY LOCATIONS
- **Code:** `alphagenesis/features/sdm_engine.py` (core engine)
- **State:** `/tmp/bandit_state.json` (strategy learning)
- **Service:** `sudo systemctl status sdm-trading.service`
- **Logs:** `sudo journalctl -u sdm-trading.service -o cat -f`

## OPTIMIZATION TARGETS (Final Sprint)
1. **Signal Quality** - Are we catching the right moves?
2. **Position Sizing** - Regime-aware, aggressive but safe
3. **Execution Speed** - No delays in order placement
4. **Risk Management** - Not too conservative, not reckless
5. **Strategy Selection** - Momentum performing well?

## ASK YOURSELF
- What's the user trying to optimize?
- Do I need more context? (Read CLAUDE.md or CLAUDE_CONTEXT_MEMORY.md)
- Should I check system health first?
- Is this an emergency or optimization task?

---

**NOW GO WIN THIS COMPETITION**
