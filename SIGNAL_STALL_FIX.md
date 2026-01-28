# Signal Stall Emergency Fix - Deployment Guide

## Critical Issue Diagnosed

**Symptom:** Trading system generated ZERO signals for 4+ hours
- No DIAG_ACTION logs
- Only AI_EXIT_LOG_WIRED heartbeats
- No orders placed
- No WEEX_ORDER_RESPONSE logs

## Root Cause Analysis

### What the Experts Thought
The three experts (Codex, DeepSeek, Chat) suggested:
1. Regime detector stuck in LOW_VOLATILITY with hard gate
2. Data feed stalled
3. Loop not iterating

### Actual Root Cause
**The Contextual Bandit learned that 'flat' (no trading) is better than 'momentum' strategy.**

#### Evidence Chain
1. **Bandit Architecture** (sdm_engine.py:156-162)
   - Strategies: `['momentum', 'flat']`
   - Algorithm: Upper Confidence Bound (UCB)
   - Learns from rewards over time

2. **Signal Generation Flow** (sdm_engine.py:664-683)
   ```python
   chosen_strategy = self.bandit.select_strategy(symbol, regime_str)  # Line 667

   if chosen_strategy == 'flat':  # Line 672
       return {'direction': 'HOLD', 'confidence': 0.0, 'strategy': 'flat'}  # Line 674
   ```

3. **Execution Skip** (sdm_engine.py:538-539)
   ```python
   if not proposed_action or proposed_action.get('direction') == 'HOLD':
       continue  # Skips entire execution pipeline
   ```

4. **Result:** Bandit selecting 'flat' → HOLD → no signals → complete stall

### Why Did Bandit Learn This?
If recent 'momentum' trades lost money (due to market conditions, stops being hit, etc.), the bandit's UCB algorithm would:
1. Calculate: `mean_reward('momentum')` < `mean_reward('flat')`
2. Where `mean_reward('flat')` = 0.0 (no losses from not trading)
3. Select 'flat' as optimal strategy
4. Continue selecting 'flat' until exploration forces a momentum try

**Important:** There is NO LOW_VOLATILITY hard gate in the codebase. The experts' diagnosis was incorrect.

## The Fix

### Code Changes (Already Committed)

**1. Force Momentum-Only Mode** (sdm_engine.py:157)
```python
# Before:
strategies=['momentum', 'flat']

# After:
strategies=['momentum']  # FORCE MOMENTUM ONLY
```

**2. Add Diagnostic Logging** (sdm_engine.py:664-690)
New logs to track signal generation:
- `DIAG_STRATEGY_SELECT`: Shows which strategy bandit chose
- `DIAG_FLAT_SELECTED`: Logs when 'flat' was chosen (should never see now)
- `DIAG_NO_SIGNAL`: Logs when momentum engine returns None
- `DIAG_SIGNAL_GENERATED`: Confirms signal creation
- `DIAG_HOLD_SKIP`: Tracks actions skipped due to HOLD

**3. Emergency Unstall Script** (emergency_unstall.sh)
- Stops service
- Resets bandit state (clears learned 'flat' preference)
- Restarts service
- Provides verification commands

## Deployment Instructions

### Step 1: Pull Latest Code
```bash
cd /opt/AlphaGenesis
git fetch origin
git checkout claude/weex-trading-system-JjDSY
git pull origin claude/weex-trading-system-JjDSY
```

### Step 2: Run Emergency Unstall
```bash
./emergency_unstall.sh
```

This will:
1. Stop the trading service
2. Backup and delete `/tmp/bandit_state.json` (contains learned 'flat' preference)
3. Restart the service with fixed code
4. Show service status

### Step 3: Verify Fix (Critical!)

**Monitor for signal generation:**
```bash
sudo journalctl -u sdm-trading.service -o cat -f | \
  egrep -i 'DIAG_STRATEGY_SELECT|DIAG_SIGNAL_GENERATED|DIAG_NO_SIGNAL|Placing order|WEEX_ORDER_RESPONSE' \
  --line-buffered --color=always
```

**Expected within 5-10 minutes:**
- ✅ `DIAG_STRATEGY_SELECT: ... strategy=momentum` (bandit choosing momentum)
- ✅ `DIAG_SIGNAL_GENERATED: ... direction=LONG/SHORT` (signals being created)
- ✅ `Placing order for ...` (execution pipeline)
- ✅ `WEEX_ORDER_RESPONSE` (order confirmations)

**If you see instead:**
- ❌ `DIAG_NO_SIGNAL` repeatedly → Momentum engine itself is failing
  - Check market data availability
  - Check if candles have sufficient history (needs 50+)
  - Verify MomentumHybridEngine thresholds aren't too extreme

### Step 4: Check Signal Distribution (After 30 mins)
```bash
sudo journalctl -u sdm-trading.service -o cat --since "30 minutes ago" | \
  grep "DIAG_SIGNAL_GENERATED" | wc -l
```

**Expected:** 5-20 signals (depending on market conditions and symbols)

**If zero:** Run deeper diagnostics:
```bash
# Check if momentum engine is returning None
sudo journalctl -u sdm-trading.service -o cat --since "30 minutes ago" | \
  grep "DIAG_NO_SIGNAL"

# Check regime distribution
sudo journalctl -u sdm-trading.service -o cat --since "30 minutes ago" | \
  grep "regime=" | awk -F"regime=" '{print $2}' | awk '{print $1}' | sort | uniq -c
```

## Fallback Plans

### If Signals Still Zero After 30 Minutes

The issue is deeper than bandit selection. Possibilities:

**A. Momentum Engine Thresholds Too Strict**
- File: `alphagenesis/features/momentum_hybrid_engine.py`
- Lines 126-129 (LONG conditions), 151-154 (SHORT conditions)
- Current thresholds:
  - LONG: `rsi > 55`, `momentum_pct > 1.0`
  - SHORT: `rsi < 45`, `momentum_pct < -1.0`
- **Quick Fix:** Lower momentum threshold to 0.5% (from 1.0%)

**B. Market Data Feed Issue**
- Check if candles are being fetched: `grep "get_candles" logs`
- Check if tickers are updating: `grep "get_ticker" logs`
- Verify WEEX API connection: Check for API errors in logs

**C. Intent Graph Blocking**
- The intent graph might be rejecting all actions
- Check: `grep "Intent graph rejected" logs`
- If present, review intent_graph.py constraints

### Full Reset (Last Resort)
```bash
./emergency_unstall.sh --full-reset
```

This also clears:
- Position ledger (`/tmp/position_ledger.json`)
- Decision journal (`/tmp/trading_journal.db`)

Use only if you suspect corrupted state files.

## Expected Competition Impact

### Current State (Before Fix)
- **4+ hours of zero trading** = significant ranking loss
- Competitors actively trading and gaining P&L
- Every hour counts in AI Wars competition

### After Fix (Best Case)
- **Immediate signal generation** within 5-10 minutes
- **Resume active trading** across all 8 symbols
- **Bandit re-learns** from fresh state (momentum-only)
- **Catch up opportunity** if market conditions favorable

### After Fix (Worst Case)
- If momentum engine is fundamentally broken, signals still zero
- Would require deeper strategy changes (beyond scope of this fix)
- Escalate to momentum engine diagnostic protocol

## Monitoring Commands (First Hour)

### Every 5 Minutes
```bash
# Signal count
sudo journalctl -u sdm-trading.service -o cat --since "5 minutes ago" | \
  grep "DIAG_SIGNAL_GENERATED" | wc -l
```

### Every 15 Minutes
```bash
# Order execution count
sudo journalctl -u sdm-trading.service -o cat --since "15 minutes ago" | \
  grep "Placing order" | wc -l

# Check for errors
sudo journalctl -u sdm-trading.service -o cat --since "15 minutes ago" | \
  grep -i "error\|exception\|failed" | tail -20
```

### After 1 Hour
```bash
# Full diagnostic report
sudo journalctl -u sdm-trading.service -o cat --since "1 hour ago" | \
  egrep -i "DIAG_SIGNAL_GENERATED|Placing order|WEEX_ORDER_RESPONSE|P&L" | \
  tail -100
```

## What to Report Back

After deployment, please share:

1. **Immediate (within 10 minutes):**
   - Output of DIAG_* monitoring command
   - Any DIAG_SIGNAL_GENERATED logs seen?
   - Any order placement logs?

2. **After 30 minutes:**
   - Signal count from last 30 minutes
   - Order count from last 30 minutes
   - Any errors encountered?

3. **After 1 hour:**
   - Full diagnostic report output
   - Current P&L change (if any)
   - Next steps needed?

## Technical Notes

### Why Remove 'flat' Instead of Resetting Bandit?
- Resetting alone would work temporarily, but bandit would re-learn 'flat' if market continues unfavorable
- Removing 'flat' forces system to keep trading (competition requirement)
- Better to have small losses than zero activity in a competition

### Can We Re-Add 'flat' Later?
- Yes, but only after:
  1. Momentum strategy proves profitable over 100+ trades
  2. Bandit has strong positive rewards for momentum
  3. Competition is secure enough to allow "sit out" periods
- Current priority: **Get back to trading immediately**

### Bandit State File Location
- Path: `/tmp/bandit_state.json`
- Contains: Per-context (symbol, regime) arm statistics
- Resets: On service restart after file deletion
- Backup: Automatically created by emergency_unstall.sh

## Next Optimization (After Signals Restored)

Once signals are flowing again (even if losing money):

1. **Review stop-loss widths** - Might be too tight, causing frequent losses
2. **Review momentum thresholds** - Might be catching false breakouts
3. **Review regime detection** - Might be misclassifying market conditions
4. **Review position sizing** - Recently increased, might be hitting margin limits

But first: **Get signals flowing**. Can't optimize what isn't running.

---

**DEPLOY NOW. Every minute without trading = ranking loss.**

Run:
```bash
./emergency_unstall.sh
```

Then monitor for DIAG_SIGNAL_GENERATED logs.

Report results in 10 minutes.
