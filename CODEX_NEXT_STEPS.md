# CODEX: IMMEDIATE ACTIONS - LOW_VOL OVERRIDE VERIFICATION

**Status:** 2nd place (fell from 1st)
**Last Deployment:** LOW_VOL override in `/opt/AlphaGenesis/alphagenesis/sdm/sdm_engine.py`
**SSH Warning:** VM resource constrained - single session only

---

## STEP 1: Verify Override is Working (2 minutes)

Run this verification command:

```bash
sudo journalctl -u sdm-trading.service -o cat --since "2 minutes ago" | \
  egrep -i "LOW_VOL OVERRIDE|DIAG_MOMENTUM|DIAG_ACTION|Placing order:|WEEX_ORDER_RESPONSE" | tail -80
```

### What to Look For:

**✅ SUCCESS INDICATORS:**
- `LOW_VOL OVERRIDE: forcing chosen_strategy=momentum` logs appearing
- `DIAG_MOMENTUM` or `DIAG_ACTION` logs showing signals generated
- `Placing order:` logs showing trades executed
- `WEEX_ORDER_RESPONSE` confirming orders placed

**❌ FAILURE INDICATORS:**
- No `LOW_VOL OVERRIDE` logs → Override not triggering (check regime detection)
- `LOW_VOL OVERRIDE` appears but no signals → Momentum thresholds too strict
- Signals appear but no orders → Intent graph or execution blocking

---

## STEP 2: If Override Working But No Signals

The momentum thresholds might be too strict in LOW_VOL conditions.

**Current thresholds** (in `momentum_hybrid_engine.py`):
- RSI > 55 for LONG
- RSI < 45 for SHORT
- Momentum > 1.0% or < -1.0%

### Check Actual Market Values

```bash
# See what RSI/momentum values are being calculated
sudo journalctl -u sdm-trading.service -o cat --since "5 minutes ago" | \
  grep -i "RSI\|momentum" | tail -30
```

### Threshold Adjustment Strategy

If you see patterns like:
- `RSI=52` but threshold is 55 → **Lower LONG threshold to 52**
- `RSI=48` but threshold is 45 → **Raise SHORT threshold to 48**
- `momentum=0.7%` but threshold is 1.0% → **Lower to 0.6%**

**File to edit:** `/opt/AlphaGenesis/alphagenesis/features/momentum_hybrid_engine.py`

Look for signal generation logic (around lines 80-120) and adjust thresholds.

---

## STEP 3: If No LOW_VOL Override Logs

The regime might not be detecting LOW_VOLATILITY. Check current regime:

```bash
sudo journalctl -u sdm-trading.service -o cat --since "3 minutes ago" | \
  grep -i "regime" | tail -20
```

**If seeing other regimes (TRENDING, RANGING, etc.):**
- System is trading in those regimes normally
- LOW_VOL override only helps when in LOW_VOLATILITY regime
- May need to tune OTHER regime thresholds instead

---

## STEP 4: Quick Competition Analysis

```bash
# How many signals in last 15 minutes?
sudo journalctl -u sdm-trading.service -o cat --since "15 minutes ago" | \
  grep "DIAG_SIGNAL_GENERATED" | wc -l

# Any errors blocking trading?
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | \
  grep -i "error\|exception\|failed" | tail -10

# Account status
cd /opt/AlphaGenesis && python3 scripts/check_weex_account.py
```

---

## DECISION TREE

```
Run STEP 1 verification command
│
├─ See "LOW_VOL OVERRIDE" logs?
│  ├─ YES → See signals/orders after override?
│  │  ├─ YES → ✅ Working! Monitor P&L recovery
│  │  └─ NO → STEP 2: Lower momentum thresholds
│  │
│  └─ NO → STEP 3: Check current regime
│     ├─ In LOW_VOL? → Override not firing, check code
│     └─ Other regime? → Tune THAT regime's thresholds
│
└─ Run STEP 4 to understand overall signal rate
```

---

## SINGLE BEST NEXT ACTION

Based on verification output, pick ONE adjustment:

1. **If override working, just wait** → Monitor for 5-10 min, let trades execute
2. **If no signals in LOW_VOL** → Lower momentum threshold from 1.0% to 0.6%
3. **If not in LOW_VOL regime** → Check what regime we're in, tune that
4. **If signals blocked** → Check intent graph constraints or execution errors

---

## SSH Resource Warning

VM crashed on 2nd SSH session - work in single terminal:
- Use `tmux` or `screen` if you need multiple views
- Avoid opening second SSH
- Monitor resource usage: `free -h` and `top`

---

## Files Changed So Far

**Production:** `/opt/AlphaGenesis/alphagenesis/sdm/sdm_engine.py`
- Added LOW_VOL override after bandit selection
- Backup: `sdm_engine.py.bak.low_vol_override.<timestamp>`

**Next Likely Edit:** `/opt/AlphaGenesis/alphagenesis/features/momentum_hybrid_engine.py`
- If signals not generating, lower thresholds

---

## Paste Output Here

Run the STEP 1 verification command and paste the last 80 lines.
I'll tell you the single best next adjustment to reclaim 1st place.

**LET'S GET BACK ON TOP.**
