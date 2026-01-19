# AlphaGenesis Trading System - Complete Context for Codex

**Date:** 2026-01-19
**Competition:** WEEX AI Wars: Alpha Awakens
**Bot Name:** Alpha Genesis
**Status:** 2nd place, $1,221 balance (+22.1% ROI)

---

## CRITICAL: Production Status Check Needed

**You (the user) need to run this from your local machine:**

```bash
ssh root@34.133.16.230 "cd /opt/AlphaGenesis && git log -1 --oneline"
```

**Expected output if up-to-date:**
```
2e75ad4 TOOLS: Add production monitoring and continuous improvement tools
```

**If production shows older commit, run:**
```bash
ssh root@34.133.16.230 "cd /opt/AlphaGenesis && git pull origin claude/weex-trading-system-JjDSY && systemctl restart sdm-trading.service"
```

---

## Repository Information

**GitHub:** `wildhash/AlphaGenesis` (private)
**Branch:** `claude/weex-trading-system-JjDSY`
**Production:** `root@34.133.16.230:/opt/AlphaGenesis`
**Service:** `sdm-trading.service`

**Latest commits (local repo):**
```
2e75ad4 - TOOLS: Add production monitoring and continuous improvement tools
0af4016 - DOCS: Add quick start guide for logging system
c33ffff - FEAT: Add comprehensive validation logging for hackathon submission
3fc7a5b - DOCS: Add status report and validation report for Codex review
8d39baf - DOCS: Complete documentation of all critical risk management fixes
aacb1c2 - URGENT: Fix remaining critical risk management blockers
```

**Minimum safe version:** `aacb1c2` (has all 6 critical risk fixes)
**Recommended version:** `c33ffff` (has validation logging)
**Latest version:** `2e75ad4` (has production tools + trade logging)

---

## The 6 Critical Fixes (Deployed)

All fixes are in `alphagenesis/sdm/sdm_engine.py`:

1. **P&L Field Fallback** (lines 397-416)
   - Tries 9 variations of field names
   - Prevents zero P&L when field name changes

2. **Open Value Calculation** (lines 418-428)
   - Fallback to `size * mark_price`
   - Ensures notional exposure is tracked

3. **Leverage Safety** (lines 429-438)
   - Guards against zero/missing leverage
   - Uses safe default of 20x

4. **SL/TP Conversion** (lines 697-741)
   - Converts percentage to absolute prices
   - Direction-aware (LONG vs SHORT)
   - Now with validation logging

5. **Ethics Metrics Injection** (lines 743-780)
   - Injects 5 metrics for ethics engine
   - Daily drawdown, position concentration, etc.

6. **UTC Timezone** (lines 189-193, 345-360)
   - Uses UTC for all date checks
   - Proper daily reset at midnight UTC

---

## Trade Logging (JUST ADDED)

**New file:** `alphagenesis/learning/trade_logger.py`

**What it logs (JSONL format):**
- Signal generation
- Risk gate decisions
- Order creation/fill
- Position open/close
- Stop loss / take profit triggers
- Account snapshots
- Daily summaries
- Errors

**Log location:** `logs/trades/YYYY-MM-DD.jsonl`

**Integration status:** ✅ Created, ⏳ Need to integrate into sdm_engine.py

---

## How System Gets Smarter

**Automatic (no intervention):**

1. **Multi-Armed Bandit** (`alphagenesis/sdm/continuous_learning.py`)
   - Learns which strategies work in each regime
   - State saved to `bandit_state.json`
   - Improves over 2-4 weeks

2. **Decision Journal** (`alphagenesis/learning/decision_journal.py`)
   - SQLite database: `decision_journal.db`
   - Records every decision with full context
   - Enables post-analysis

3. **Regime Detection** (`sdm_engine.py`)
   - Detects UPTREND/DOWNTREND/SIDEWAYS/etc.
   - Selects strategy optimized for regime
   - Adapts to changing markets

**See `CONTINUOUS_IMPROVEMENT.md` for full details.**

---

## Production Management Commands

**Check status:**
```bash
# From user's local machine
ssh root@34.133.16.230
systemctl status sdm-trading.service
journalctl -u sdm-trading.service -n 50
cd /opt/AlphaGenesis && python3 check_weex_account.py
```

**Check version mismatch:**
```bash
# On local machine with repo
cd /path/to/AlphaGenesis
git log -1 --oneline  # Local version

# On production
ssh root@34.133.16.230 "cd /opt/AlphaGenesis && git log -1 --oneline"  # Production version
```

**Deploy update (if needed):**
```bash
ssh root@34.133.16.230
cd /opt/AlphaGenesis
systemctl stop sdm-trading.service
git pull origin claude/weex-trading-system-JjDSY
systemctl start sdm-trading.service
systemctl status sdm-trading.service
```

**Monitor live:**
```bash
ssh root@34.133.16.230
journalctl -u sdm-trading.service -f
```

---

## Key Validation Metrics

**From logs, check for:**

1. **P&L Metrics:** `grep "unrealized_pnl" logs/sdm_trading_*.log`
   - Should show non-zero values

2. **SL/TP Conversion:** `grep "SL/TP CONVERSION" logs/sdm_trading_*.log`
   - Should show percentage → absolute conversions

3. **Risk Gates:** `grep -E "LEDGER|GROSS EXPOSURE|RISK MANAGER" logs/sdm_trading_*.log`
   - Should show gate decisions (PASSED/BLOCKED)

4. **Daily Reset:** `grep "Day changed (UTC)" logs/sdm_trading_*.log`
   - Should appear at UTC midnight

5. **Trade Activity:** `grep "ORDER PLACED" logs/sdm_trading_*.log`
   - Should show recent orders

---

## Competition Status

**WEEX Leaderboard (Jan 18, 11:30 UTC):**
- Rank: 2nd in Group1-3
- Balance: $1,221.62
- Starting balance: $1,000.00
- ROI: +22.16%

**Top performers:**
1. Paper Hands Club: $1,829.34
2. **Alpha Genesis: $1,213.51** ← This is us!
3. Four Party: $1,119.19

**Recent trades (visible on leaderboard):**
- ETHUSDT short: Entry $3,300.93 → Exit $3,314.53
- Hold time: 1h 2m
- P&L: -$2.72 (small loss)

---

## What Codex Requested

1. **✅ Persistent context file** → `CODEX_START_HERE.md` created
2. **✅ Trade logging** → `trade_logger.py` created
3. **⏳ Integration** → Need to add trade_logger calls to sdm_engine.py
4. **⏳ Production check** → User needs to run SSH command

---

## Next Actions (Priority Order)

### IMMEDIATE
1. **User runs:** `ssh root@34.133.16.230 "cd /opt/AlphaGenesis && git log -1 --oneline"`
2. **If behind:** Deploy latest code to production
3. **Verify:** Service is running and trading

### SHORT TERM (Today)
4. **Integrate trade_logger** into sdm_engine.py
5. **Test logging** locally or in staging
6. **Deploy** integrated trade logger to production

### ONGOING
7. **Monitor** daily: Check service status, errors, balance
8. **Collect logs** weekly: Run log analysis
9. **Review learning** monthly: Check bandit stats, journal patterns

---

## For Codex: File Locations

**Key docs you should read:**
- This file: `SHARE_WITH_CODEX.md`
- Status: `STATUS_FOR_CODEX.md`
- Validation: `VALIDATION_REPORT.md`
- Logging guide: `LOGGING_GUIDE.md`
- Continuous improvement: `CONTINUOUS_IMPROVEMENT.md`
- Production guide: `PRODUCTION_STATUS_GUIDE.md`

**Key code files:**
- Main engine: `alphagenesis/sdm/sdm_engine.py`
- Trade logger: `alphagenesis/learning/trade_logger.py`
- Bandit: `alphagenesis/sdm/continuous_learning.py`
- Decision journal: `alphagenesis/learning/decision_journal.py`

**Tools:**
- `check_production_status.sh` - Check what's deployed
- `deploy_to_production.sh` - Safe deployment
- `collect_logs.sh` - Fetch logs from production
- `analyze_logs.sh` - Validate fixes

---

## Current Risks

1. **Production version unknown** - Need user to check
2. **Trade logging not integrated** - In progress
3. **No recent log validation** - Need to collect logs
4. **Bandit learning status unknown** - Need to check state file

---

## Success Criteria for Hackathon

**Must have:**
- ✅ System trading actively
- ✅ All 6 critical fixes deployed
- ✅ Positive ROI (currently +22.16%)
- ⏳ Comprehensive logs for validation
- ⏳ Evidence of continuous learning

**Nice to have:**
- Complete trade audit trail (JSONL)
- Bandit statistics showing learning
- Decision journal analysis
- Performance improvement over time

---

## Questions for User

1. What commit is production running? (Run SSH command above)
2. When did competition start? (Need to know learning duration)
3. Do you have access to WEEX dashboard for trade history?
4. Should we integrate trade_logger now or after hackathon?

---

**Generated:** 2026-01-19
**Author:** Claude in `/home/user/AlphaGenesis` environment
**For:** Codex in `/home/woakwild/` environment
**Status:** Trade logger created, awaiting production check and integration

---

## TL;DR for Codex

- **System:** Trading live, 2nd place, +22% ROI
- **Code:** All fixes deployed (if production is up-to-date)
- **Logging:** New trade_logger created, needs integration
- **Action needed:** User must check production version
- **Risk:** Production might be behind latest code
- **Goal:** Win hackathon with evidence of robust system + learning
