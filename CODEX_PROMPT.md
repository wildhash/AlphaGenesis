# CODEX EXECUTION PROMPT - Regime-Aware Position Sizing Verification

## MISSION: Verify and monitor the regime-aware position sizing deployment to close the $144-150 leaderboard gap

## PHASE 1: IMMEDIATE VERIFICATION (Next 5-10 minutes)

### Task 1A: Verify Sizing Multiplier Math
```bash
# CRITICAL: Check if multiplier is correctly implemented
# Expected: base_risk (1%) * multiplier = 2.5% (which is 2.5x, NOT 1.67x)
grep -rn "size_multiplier" /home/wildhash/alphagenesis/ --include="*.py" | head -20
grep -rn "STRONG_UPTREND detected" /home/wildhash/alphagenesis/ --include="*.py" | head -20
grep -rn "regime_sizing\|position_size.*regime" /home/wildhash/alphagenesis/ --include="*.py" | head -20
```

**VERIFICATION CHECKPOINT:**
- If multiplier shows 1.67x → ALERT: Math is wrong, should be 2.5x
- If multiplier shows 2.5x or 2.50 → CONFIRMED: Correct implementation

### Task 1B: Confirm Deployment is Live
```bash
# Check if service is running with latest code
sudo systemctl status sdm-trading.service | grep -A 3 "Active:"

# Check service log for regime-aware sizing evidence
sudo journalctl -u sdm-trading.service --since "5 minutes ago" -o cat | \
  grep -E "STRONG_UPTREND detected|size multiplier|Position sizing.*%" | tail -20

# If no logs found, check alternative log location
tail -100 /var/log/weex-trading/service.log | grep -E "STRONG_UPTREND|multiplier|Position sizing"
```

**DECISION POINT:**
- ✅ If you see sizing multiplier logs → Deployment is LIVE
- ❌ If NO sizing logs after 10 mins → Service needs restart:
  ```bash
  sudo systemctl restart sdm-trading.service
  ```

---

## PHASE 2: ACTIVE MONITORING (Next 60-90 minutes)

### Task 2A: Live Trade Monitoring
```bash
# Monitor live for STRONG_UPTREND trades with new sizing
sudo journalctl -u sdm-trading.service -o cat -f | \
  egrep -i "STRONG_UPTREND detected|Position sizing|size multiplier|DIAG_ACTION|WEEX_ORDER_RESPONSE|AI_EXIT_LOG|P&L" --line-buffered --color=always
```

**WATCH FOR:**
- 📊 "STRONG_UPTREND detected - applying [X]x size multiplier"
- 💰 "Position sizing: 2.50% of $[balance] = $[size]"
- 📈 Trade fills showing LARGER position sizes than before
- 🎯 P&L updates showing bigger wins (or losses)

### Task 2B: Leaderboard Gap Tracking
```bash
# Check leaderboard every 15 minutes
watch -n 900 'curl -s https://tradingcompetition.example.com/leaderboard | grep -A 5 "your_username"'
```

**TRACK:**
- Current gap to leader: $____
- Rate of change: Is gap shrinking/stable/widening?

---

## PHASE 3: DECISION GATE (After 60 minutes)

### Outcome Assessment Matrix

Run this analysis after 60 minutes:

```bash
# Get last 10 STRONG_UPTREND trades
sudo journalctl -u sdm-trading.service --since "60 minutes ago" -o cat | \
  grep -E "STRONG_UPTREND detected|ORDER_FILLED|EXIT.*profit|P&L" | tail -50
```

**DECISION LOGIC:**

| Gap Status | Trade Quality | Next Action | Code |
|------------|---------------|-------------|------|
| Shrinking (>$20 improvement) | N/A | ✅ **HOLD COURSE** - Strategy working | NONE |
| Stable (±$20) | Mixed/Positive | ⚡ **BACKUP #1** - Relax momentum threshold | B1 |
| Stable (±$20) | Mostly losses | 🔍 **DIAGNOSE** - Check signal quality | DIAG |
| Widening (>$20 worse) | N/A | 🚨 **REVERT** - Abort sizing increase | REVERT |
| Shrinking but slow | 3+ wins | 🔥 **BACKUP #2** - Increase to 3% size | B2 |

---

## CONTINGENCY CODES

### REVERT: Emergency Rollback
```bash
cd /home/wildhash/alphagenesis
# Find the position sizing logic
grep -rn "size_multiplier.*2.5\|size_multiplier.*1.67" . --include="*.py"
# Manually set multiplier back to 1.0 in the file shown above
# Then restart:
sudo systemctl restart sdm-trading.service
```

### B1: Backup Plan #1 - Relax STRONG_UPTREND Threshold
**Use if: Gap stable after 60 mins + trade frequency too low**

```bash
cd /home/wildhash/alphagenesis
# Find momentum threshold for STRONG_UPTREND
grep -rn "STRONG_UPTREND.*0.3\|long_momentum_threshold.*0.3" . --include="*.py"
# Edit the file to change:
# FROM: long_momentum_threshold = 0.3  (or 0.4)
# TO:   long_momentum_threshold = 0.25
# Expected: +15-25% more STRONG_UPTREND signals
sudo systemctl restart sdm-trading.service
```

### B2: Backup Plan #2 - Escalate Size to 3%
**Use if: First 3-5 STRONG_UPTREND trades are net profitable but gap closing too slowly**

```bash
cd /home/wildhash/alphagenesis
# Find size_multiplier
grep -rn "size_multiplier.*STRONG_UPTREND" . --include="*.py"
# Edit to change:
# FROM: size_multiplier = 2.5  (or whatever it currently is)
# TO:   size_multiplier = 3.0
sudo systemctl restart sdm-trading.service
```

### DIAG: Signal Quality Diagnosis
```bash
# Analyze last 10 STRONG_UPTREND trades
sudo journalctl -u sdm-trading.service --since "90 minutes ago" -o cat | \
  grep -B 2 -A 8 "STRONG_UPTREND detected" | \
  grep -E "detected|ORDER|profit|loss|P&L"

# Questions to answer:
# 1. How many STRONG_UPTREND trades executed?
# 2. Win rate of these trades?
# 3. Were losses small (stops working) or large (stops failing)?
# 4. Are we entering at poor prices?
```

---

## CRITICAL MATH CHECK

Before proceeding, confirm:

```bash
# Expected calculation:
# base_risk = 1.0%
# STRONG_UPTREND multiplier = 2.5
# final_risk = 1.0% * 2.5 = 2.5%

# If logs show "1.67x multiplier" with "2.5% position":
# Then base_risk is actually 1.5% (which is wrong)
# Base risk should be 1.0% for proper scaling
```

**ACTION IF MATH IS WRONG:**
Find and fix base risk calculation to ensure clean 1% → 2.5% scaling.

---

## SUCCESS METRICS (Report after 90 minutes)

Provide this report:

```
SIZING VERIFICATION REPORT
==========================
Deployment Time: [timestamp]
Current Time: [timestamp]
Elapsed: [X] minutes

IMPLEMENTATION:
✓/✗ Size multiplier found in code: [value]
✓/✗ Math verified (1% → 2.5% = 2.5x): [YES/NO]
✓/✗ Logs showing regime-aware sizing: [YES/NO]

PERFORMANCE:
- Starting gap: $[X]
- Current gap: $[X]
- Delta: $[X] ([improving/worsening])
- STRONG_UPTREND trades: [count]
- Win rate: [X]%
- Largest win: $[X]
- Largest loss: $[X]

DECISION: [HOLD/B1/B2/REVERT/DIAG]
REASONING: [1-2 sentences]
```

---

## IMMEDIATE NEXT STEPS

1. **Run Task 1A** to verify multiplier math
2. **Run Task 1B** to confirm deployment
3. **Execute Task 2A** in a persistent terminal (tmux/screen recommended)
4. **Wait 60 minutes** while monitoring
5. **Run Decision Gate** assessment
6. **Execute contingency** if needed

**START NOW. Time is critical in a competition.**
