# Trading System Restart Guide
**Date:** 2026-02-28
**Status:** System restarted after several days offline
**Branch:** `claude/weex-trading-system-JjDSY`

## Current Situation

✅ **Service is running** - Started at `01:46:03 UTC`
⏳ **First iteration in progress** - Update interval is 5 minutes
📝 **State files pending** - Will be created after first iteration completes
🔍 **Need to verify** - Signal generation and order placement

## Why State Files Don't Exist Yet

The system uses **lazy file creation**:
- State files are only written when there's data to save
- First iteration takes 5 minutes (UPDATE_INTERVAL=300s)
- After 5 minutes, files should appear:
  - `/tmp/bandit_state.json` - Strategy learning
  - `/tmp/position_ledger.json` - Position tracking
  - `/tmp/trading_journal.db` - Already exists ✅

## What to Monitor

### 1. Wait for First Iteration (5 minutes from start)
```bash
# Check if first iteration completed
sudo journalctl -u sdm-trading.service -o cat | grep "SDM ITERATION"

# Expected: Should see "SDM ITERATION 1" then "SDM ITERATION 2" after 5 min
```

### 2. Verify Signal Generation
```bash
# Count signals in last 15 minutes
sudo journalctl -u sdm-trading.service -o cat --since "15 minutes ago" | \
  grep "DIAG_SIGNAL_GENERATED" | wc -l

# Expected: Should see signals being generated
```

### 3. Check for Errors
```bash
# Look for any errors
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | \
  grep -i "error\|exception\|traceback"

# Expected: No critical errors
```

### 4. Monitor Live Activity
```bash
# Watch live signal generation
sudo journalctl -u sdm-trading.service -o cat -f | \
  egrep 'DIAG_SIGNAL_GENERATED|Placing order|WEEX_ORDER_RESPONSE' \
  --line-buffered --color=always
```

### 5. Check Account Status
```bash
cd /opt/AlphaGenesis && python3 scripts/check_weex_account.py
```

## Quick Health Check

Run the automated health check:
```bash
cd /home/user/AlphaGenesis
./check_system_health.sh
```

## Expected Timeline

| Time | Event | What to Check |
|------|-------|---------------|
| `01:46:03` | Service started | ✅ Service active |
| `01:51:03` | First iteration done | State files created |
| `01:56:03` | Second iteration | Signals generated |
| `02:01:03` | Third iteration | Orders placed |

## Potential Issues to Watch

### Issue 1: No Signals Generated
**Symptom:** `DIAG_SIGNAL_GENERATED` count = 0 after 10+ minutes
**Cause:** Possible regime detection blocking trades
**Check:**
```bash
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | \
  grep "regime"
```

### Issue 2: Bandit Learning 'flat' Again
**Symptom:** All signals show `strategy: 'flat'`
**Cause:** Bandit learned to avoid trading (the old bug)
**Check:**
```bash
cat /tmp/bandit_state.json | jq '.context_arms'
```
**Expected:** Should only see `momentum` strategy, NO `flat`

### Issue 3: Service Crashes
**Symptom:** Service status shows `failed` or `inactive`
**Check:**
```bash
sudo systemctl status sdm-trading.service
sudo journalctl -u sdm-trading.service -o cat --since "1 hour ago" | tail -50
```

## Last Known Commit in Production

```bash
$ cd /opt/AlphaGenesis && git log -1 --oneline
02e44b7 docs(postmortem): record 2026-02-23 SOL breakout miss root cause
```

This is from several days ago (2026-02-23). The system was stopped and is now restarting.

## Competition Status

⚠️ **Competition may have ended** - It's been several days since last activity
📅 **Last active:** Around 2026-02-23
📅 **Current date:** 2026-02-28

**Action:** Verify if competition is still running:
1. Check WEEX account for trading activity
2. Look at competition leaderboard
3. Verify if trades are being accepted

## Next Steps

1. **Immediate (Now):**
   - Run health check: `./check_system_health.sh`
   - Wait for first iteration to complete (~2 more minutes from your last check)
   - Check state files appear: `ls -lh /tmp/*.json /tmp/*.db`

2. **After 10 minutes:**
   - Verify signals: `grep DIAG_SIGNAL_GENERATED`
   - Check orders: `grep "Placing order"`
   - Monitor account P&L

3. **If Issues Found:**
   - Check logs for errors
   - Verify environment variables set
   - Check WEEX API connectivity
   - Review bandit state for 'flat' strategy

4. **If System Healthy:**
   - Monitor for next few hours
   - Track P&L performance
   - Optimize if needed

## Need Help?

If you see errors or unexpected behavior:
1. Run: `./check_system_health.sh > health_report.txt`
2. Check the report for errors
3. Look at CLAUDE_CONTEXT_MEMORY.md for troubleshooting tips
4. Review SIGNAL_STALL_FIX.md if signals aren't generating

---

**Remember:** The system needs 5 minutes to complete first iteration.
**Be patient** and let it run before diagnosing issues.
