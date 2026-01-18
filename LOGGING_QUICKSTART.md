# Logging System - Quick Start

## For Final Hackathon Submission

### Step 1: Collect Production Logs (5 minutes)

```bash
bash collect_logs.sh
```

**Creates:**
- `hackathon_logs_YYYYMMDD_HHMMSS/` directory
- `hackathon_logs_YYYYMMDD_HHMMSS.tar.gz` archive

**Contains:**
- All production log files
- Systemd journal logs
- System status snapshot
- Account state data

---

### Step 2: Analyze Logs (2 minutes)

```bash
bash analyze_logs.sh
```

**Creates:**
- `log_analysis_report_YYYYMMDD_HHMMSS.md`

**Validates:**
1. ✅ P&L field fallback working
2. ✅ Open value calculation working
3. ✅ Leverage safety working
4. ✅ SL/TP conversion working
5. ✅ Ethics metrics injection working
6. ✅ UTC timezone working

---

### Step 3: Review Results

Open the analysis report:
```bash
cat log_analysis_report_*.md
```

**Expected Results:**
- **Passed:** 4-6 checks
- **Warnings:** 0-2 (acceptable if system hasn't crossed UTC midnight yet)
- **Failed:** 0

---

## What Gets Logged

### 📊 Validation Metrics (every 10 iterations)
```
📊 VALIDATION METRICS:
   unrealized_pnl: $-2.30
   total_notional: $660.18
   margin_used: $44.01
```

### 🎯 SL/TP Conversion (every trade signal)
```
🎯 SL/TP CONVERSION: ETHUSDT SHORT
   Entry price: $3,300.93
   Stop Loss: 2.0% → $3,366.95
```

### 📋 Ethics Metrics (every action)
```
📋 ETHICS METRICS INJECTED:
   daily_drawdown: 0.50%
   position_concentration: 54.00%
```

### ✅ Risk Gates (every trade)
```
✅ LEDGER GATE: PASSED
✅ GROSS EXPOSURE CHECK: PASSED (18.5% < 30.0%)
✅ RISK MANAGER VETO: PASSED
```

---

## Hackathon Submission Package

Include these files:
1. `hackathon_logs_*.tar.gz` - Log archive
2. `log_analysis_report_*.md` - Validation report
3. `STATUS_FOR_CODEX.md` - Status summary
4. `VALIDATION_REPORT.md` - Validation details
5. `CRITICAL_FIXES_COMPLETE.md` - Implementation docs
6. Link to code: `alphagenesis/sdm/sdm_engine.py` lines 189-915

---

## Troubleshooting

**Q: "Cannot connect to GCP"**
```bash
ssh root@34.133.16.230  # Test connection first
```

**Q: "No validation data in logs"**
- System may not have generated signals yet
- Wait for more trading activity
- Collect logs again after a few hours

**Q: "Missing UTC daily reset"**
- Normal if haven't crossed UTC midnight
- Mark as "Pending - will occur at 00:00 UTC"

---

## For More Details

See `LOGGING_GUIDE.md` for comprehensive documentation.

---

**Quick Command Reference:**

```bash
# Collect logs
bash collect_logs.sh

# Analyze logs
bash analyze_logs.sh

# View live production logs
ssh root@34.133.16.230 'journalctl -u sdm-trading.service -f'

# Check production status
ssh root@34.133.16.230 'systemctl status sdm-trading.service'
```

---

**Generated:** 2026-01-18
**Competition:** WEEX AI Wars: Alpha Awakens
**Bot:** Alpha Genesis
