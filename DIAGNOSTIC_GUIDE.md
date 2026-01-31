# DIAGNOSTIC GUIDE - No Output in 2-Minute Window

**Situation:** Verification command returned no matches in last 2 minutes
**Next:** Run 10-minute window with expanded search patterns

---

## Command to Run Now

```bash
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | \
  egrep -i "LOW_VOL OVERRIDE|DIAG_MOMENTUM|DIAG_ACTION|DIAG_ENTRY|regime=|Placing order:|WEEX_ORDER_RESPONSE" | tail -200
```

---

## What to Look For in Output

### SCENARIO 1: Service Running, Loop Active
**Pattern:** You see `DIAG_ENTRY` or heartbeat logs
**Diagnosis:** Service is alive, but not generating signals
**Next Action:**
- Check what regime is detected: Look for `regime=` in output
- If `regime=LOW_VOLATILITY` → Override should fire, check code
- If other regime → Need to tune THAT regime's thresholds

### SCENARIO 2: LOW_VOL Override Firing
**Pattern:** You see `LOW_VOL OVERRIDE: forcing chosen_strategy=momentum`
**Diagnosis:** Override working, but momentum not generating signals
**Next Action:**
- Lower momentum thresholds in `/opt/AlphaGenesis/alphagenesis/features/momentum_hybrid_engine.py`
- Change from 1.0% to 0.6% or 0.5%
- Look for actual momentum values in logs to calibrate

### SCENARIO 3: Different Regime Active
**Pattern:** You see `regime=TRENDING` or `regime=RANGING` or `regime=MEDIUM_VOLATILITY`
**Diagnosis:** Not in LOW_VOL, so override isn't relevant right now
**Next Action:**
- The current regime's signal generation is the problem
- Need to tune thresholds for the ACTIVE regime
- May need to check if regime detection is correct

### SCENARIO 4: No DIAG Logs at All
**Pattern:** No `DIAG_ENTRY`, `DIAG_ACTION`, `DIAG_MOMENTUM` in 10 minutes
**Diagnosis:** Either service crashed or diagnostic logging removed
**Next Action:**
- Check service status: `sudo systemctl status sdm-trading.service`
- Look for Python errors: `sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | grep -i "error\|exception\|traceback" | tail -50`
- May need service restart

### SCENARIO 5: Service Errors
**Pattern:** You see Python tracebacks or import errors
**Diagnosis:** Code change broke something
**Next Action:**
- Read the error carefully
- Likely syntax error or import issue in recent changes
- May need to restore from backup: `sdm_engine.py.bak.low_vol_override.<timestamp>`

---

## Quick Triage Commands

If you need to investigate further based on what you find:

```bash
# Is service running?
sudo systemctl status sdm-trading.service

# Any Python errors?
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | \
  grep -i "error\|exception\|traceback" | tail -50

# Just show me ALL recent logs
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | tail -100

# What's the service doing RIGHT NOW?
sudo journalctl -u sdm-trading.service -o cat -f

# Check if process is running
ps aux | grep sdm
```

---

## Expected vs. Actual

### HEALTHY SYSTEM (Expected):
```
DIAG_ENTRY: Starting trading loop iteration
Regime detected: regime=LOW_VOLATILITY for BTCUSDT
LOW_VOL OVERRIDE: forcing chosen_strategy=momentum for BTCUSDT
DIAG_MOMENTUM: Checking momentum conditions...
DIAG_ACTION: Signal generated: LONG, confidence=0.75
Placing order: BTCUSDT LONG, size=0.01
WEEX_ORDER_RESPONSE: Order placed successfully, ID=12345
```

### WHAT WE'RE SEEING (Actual):
```
(empty - no logs in last 2 minutes)
```

This means the loop either:
- Isn't running at all (service down)
- Running but no DIAG logs (logging removed or suppressed)
- Running but outside our 2-minute window (very slow loop?)

---

## Decision Tree Based on 10-Minute Output

```
Run 10-minute diagnostic command
│
├─ See DIAG_ENTRY or heartbeat?
│  ├─ YES → Service running
│  │  ├─ See "LOW_VOL OVERRIDE"?
│  │  │  ├─ YES → Override working, lower momentum thresholds
│  │  │  └─ NO → Check regime, tune active regime's thresholds
│  │  │
│  │  └─ No signals at all? → Check for Python errors or intent graph blocking
│  │
│  └─ NO → Service may be stalled/crashed
│     ├─ Check: sudo systemctl status sdm-trading.service
│     ├─ Look for errors in logs
│     └─ May need: sudo systemctl restart sdm-trading.service
│
├─ See Python errors/tracebacks?
│  └─ YES → Code broke, restore backup or fix syntax error
│
└─ Completely empty logs?
   └─ Service not running or logging disabled
```

---

## Most Likely Scenarios (Ranked)

1. **Service running, wrong regime** (60% likely)
   - System is in TRENDING/RANGING, not LOW_VOL
   - Need to tune active regime's thresholds

2. **Service running, LOW_VOL but thresholds too strict** (25% likely)
   - Override fires but momentum thresholds block signals
   - Lower from 1.0% to 0.6%

3. **Service error from recent change** (10% likely)
   - Syntax error or import issue
   - Check for tracebacks, restore backup if needed

4. **Service crashed or stalled** (5% likely)
   - Process died or hung
   - Restart service

---

## Paste the 10-Minute Output

Once you run the command, paste the last 200 lines here.
I'll identify which scenario we're in and give the **single best fix**.

---

**Stay calm. One diagnostic at a time. We'll find it.**
