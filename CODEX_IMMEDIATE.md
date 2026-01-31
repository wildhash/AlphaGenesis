# CODEX: IMMEDIATE - 10-Minute Diagnostic

**Status:** No output in 2-minute window
**Next Command:** 10-minute expanded search (below)

---

## Run This Now

```bash
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | \
  egrep -i "LOW_VOL OVERRIDE|DIAG_MOMENTUM|DIAG_ACTION|DIAG_ENTRY|regime=|Placing order:|WEEX_ORDER_RESPONSE" | tail -200
```

---

## Quick Interpretation Guide

**If you see output:** Paste it and I'll tell you the fix

**If still empty:** Run these triage commands:

```bash
# Is service alive?
sudo systemctl status sdm-trading.service

# Any errors in last 10 min?
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | \
  grep -i "error\|exception\|traceback" | tail -30

# Show me raw logs (no filter)
sudo journalctl -u sdm-trading.service -o cat --since "5 minutes ago" | tail -50
```

---

## Most Likely Outcomes

### OUTCOME 1: Service Running, Wrong Regime (MOST LIKELY)
**You'll see:** Logs showing `regime=TRENDING` or `regime=RANGING`
**Meaning:** Not in LOW_VOL, so override doesn't help
**Fix:** Tune the ACTIVE regime's signal generation thresholds

### OUTCOME 2: LOW_VOL Override Firing, No Signals
**You'll see:** `LOW_VOL OVERRIDE` logs but no `DIAG_SIGNAL_GENERATED`
**Meaning:** Override working but momentum thresholds too strict
**Fix:** Lower momentum threshold from 1.0% to 0.6% in momentum_hybrid_engine.py

### OUTCOME 3: Service Error
**You'll see:** Python tracebacks or import errors
**Meaning:** Recent code change broke something
**Fix:** Restore backup or fix syntax error

### OUTCOME 4: Service Stalled/Crashed
**You'll see:** Service status "inactive" or "failed"
**Meaning:** Process died
**Fix:** `sudo systemctl restart sdm-trading.service`

---

## What I Need from You

1. **Run the 10-minute command** (first one above)
2. **Paste the output** (or say "still empty")
3. **If empty, run triage commands** and paste those

Then I'll give you **ONE ACTION** to fix it.

---

**Full diagnostic details in: DIAGNOSTIC_GUIDE.md**

**We're methodically narrowing it down. Next output will tell us everything.**
