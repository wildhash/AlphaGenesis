# AlphaGenesis Trading System - Logging Guide

**For Hackathon Submission and Validation**

---

## Overview

This guide explains how to collect, analyze, and submit logs from the AlphaGenesis trading system for the WEEX AI Wars hackathon final review.

---

## Quick Start

### Step 1: Collect Logs from Production

```bash
bash collect_logs.sh
```

This will:
- Connect to the GCP production instance (34.133.16.230)
- Download all log files
- Collect systemd journal logs
- Gather system status and account state
- Create a timestamped archive

**Output:** `hackathon_logs_YYYYMMDD_HHMMSS.tar.gz`

### Step 2: Analyze Logs

```bash
bash analyze_logs.sh
```

This will:
- Validate all 6 critical risk management fixes
- Check for errors and anomalies
- Generate a comprehensive analysis report

**Output:** `log_analysis_report_YYYYMMDD_HHMMSS.md`

---

## Logging Architecture

### Production Environment

**Location:** GCP instance `34.133.16.230`
**Project Directory:** `/opt/AlphaGenesis`
**Service:** `sdm-trading.service` (systemd)

### Log Files

1. **File-Based Logs**
   - Location: `/opt/AlphaGenesis/logs/`
   - Format: `sdm_trading_YYYY-MM-DD.log`
   - Retention: 30 days
   - Level: DEBUG (comprehensive)

2. **Systemd Journal**
   - Command: `journalctl -u sdm-trading.service`
   - Retention: System default
   - Level: INFO (console output)

---

## Validation Logging

The system now includes enhanced validation logging for all 6 critical fixes:

### Fix #1: P&L Field Fallback

**Log Pattern:** `📊 VALIDATION METRICS`

```
📊 VALIDATION METRICS:
   unrealized_pnl: $-2.30
   total_notional: $660.18
   margin_used: $44.01
   daily_pnl: $+15.42 (+1.26%)
   equity: $1,215.42
```

**Logged:** Every 10 iterations (every ~50 minutes at 5min intervals)

**Validates:**
- Unrealized P&L is being parsed (non-zero values)
- Total notional is calculated correctly
- Margin usage is computed

### Fix #2: Open Value Calculation

**Included in:** `📊 VALIDATION METRICS` → `total_notional`

**Validates:**
- Open value fallback to size * mark_price
- Non-zero notional values when positions open

### Fix #3: Leverage Safety

**No specific log (absence of errors validates)**

**Validates:**
- No `ZeroDivisionError` in logs
- System continues operating with positions
- Default 20x leverage used when missing

### Fix #4: SL/TP Conversion

**Log Pattern:** `🎯 SL/TP CONVERSION`

```
🎯 SL/TP CONVERSION: ETHUSDT SHORT
   Entry price: $3,300.93
   Stop Loss: 2.0% → $3,366.95
   Take Profit: 4.0% → $3,168.89
```

**Logged:** Every time a signal includes SL/TP percentages

**Validates:**
- Percentages converted to absolute prices
- Direction-aware (LONG vs SHORT)
- Correct price calculations

### Fix #5: Ethics Metrics Injection

**Log Pattern:** `📋 ETHICS METRICS INJECTED`

```
📋 ETHICS METRICS INJECTED:
   daily_drawdown: 0.50%
   total_drawdown: 0.00%
   position_concentration: 54.00%
   daily_trade_count: 3
   open_position_count: 1
```

**Logged:** Every time an action is generated (before execution)

**Validates:**
- All 5 ethics metrics are calculated
- Metrics are available for ethics engine
- Values are reasonable

### Fix #6: UTC Timezone

**Log Pattern:** `🌅 Day changed (UTC)`

```
🌅 Day changed (UTC) from 2026-01-17 to 2026-01-18
   Previous day P&L: $+23.45 (+1.92%)
   Daily counters reset. New baseline: $1,223.45
```

**Logged:** Once per day at UTC midnight

**Validates:**
- Daily reset uses UTC timezone
- Daily P&L percentage calculated correctly
- Counters reset at correct time

### Risk Gate Decisions

**Log Patterns:**

```
✅ LEDGER GATE: PASSED
✅ GROSS EXPOSURE CHECK: PASSED (18.5% < 30.0%)
✅ RISK MANAGER VETO: PASSED
```

or

```
🚫 LEDGER GATE: BLOCKED - Already have SHORT position in ETHUSDT
❌ GROSS EXPOSURE CHECK: BLOCKED - GROSS EXPOSURE CAP EXCEEDED: 35.2% > 30.0%
❌ RISK MANAGER VETO: BLOCKED - ['Daily trade limit exceeded']
```

**Logged:** For every proposed trade

**Validates:**
- All gates are operational
- Decision logic is working
- Limits are enforced

---

## Log Collection Details

### What `collect_logs.sh` Collects

1. **File-based logs** from `/opt/AlphaGenesis/logs/`
2. **Full systemd journal** (last 10,000 lines)
3. **Today's journal** (UTC-based)
4. **Last 24 hours journal**
5. **System status** (service, processes, resources)
6. **Account state** (via `check_weex_account.py`)
7. **Position data** (via `analyze_positions.py`)
8. **Configuration** (sanitized, no secrets)

### Directory Structure

```
hackathon_logs/
├── file_logs/
│   └── sdm_trading_2026-01-18.log
├── journal_full.log
├── journal_today.log
├── journal_24h.log
├── system_status.txt
├── account_state.txt
├── position_data.txt
├── config/
│   ├── *.yaml
│   └── env_sanitized.txt
└── METADATA.txt
```

---

## Log Analysis

### What `analyze_logs.sh` Validates

1. **Fix #1:** Non-zero unrealized P&L values
2. **Fix #2:** Non-zero notional/open value
3. **Fix #3:** No division by zero errors
4. **Fix #4:** Absolute SL/TP prices
5. **Fix #5:** Ethics metrics present
6. **Fix #6:** UTC daily reset events
7. **Risk Gates:** All gates making decisions
8. **Errors:** Count and severity of errors

### Analysis Report Format

The report includes:
- Executive summary
- Detailed validation for each fix
- Risk gate operation evidence
- Error analysis
- Overall status (PASS/FAIL/WARNING)
- Recommendations for hackathon submission

---

## Manual Log Analysis

### Common Grep Commands

```bash
# Navigate to logs
cd hackathon_logs

# Check all validation metrics
grep "VALIDATION METRICS" journal_full.log

# Check SL/TP conversions
grep "SL/TP CONVERSION" journal_full.log

# Check ethics metrics
grep "ETHICS METRICS" journal_full.log

# Check UTC daily reset
grep "Day changed (UTC)" journal_full.log

# Check risk gates
grep -E "LEDGER GATE|GROSS EXPOSURE|RISK MANAGER" journal_full.log

# Check for errors
grep -E "ERROR|CRITICAL" journal_full.log

# Check trades executed
grep "ORDER PLACED" journal_full.log
```

### Validation Checklist

- [ ] Unrealized P&L shows non-zero values
- [ ] Total notional shows non-zero values
- [ ] No ZeroDivisionError in logs
- [ ] SL/TP conversion logs present
- [ ] Ethics metrics logs present
- [ ] UTC daily reset event present (if crossed midnight)
- [ ] Ledger gate decisions present
- [ ] Gross exposure checks present
- [ ] Risk manager decisions present
- [ ] Error count is acceptable (< 10)

---

## Accessing Production Logs Directly

### SSH to Production

```bash
ssh root@34.133.16.230
```

### View Live Logs

```bash
# Follow journal in real-time
journalctl -u sdm-trading.service -f

# View today's logs
journalctl -u sdm-trading.service --since today

# View last 24 hours
journalctl -u sdm-trading.service --since "24 hours ago"

# View file logs
tail -f /opt/AlphaGenesis/logs/sdm_trading_$(date +%Y-%m-%d).log
```

### Check System Status

```bash
# Service status
systemctl status sdm-trading.service

# Account state
cd /opt/AlphaGenesis
python3 check_weex_account.py

# Position analysis
python3 analyze_positions.py
```

---

## Hackathon Submission

### Required Files

1. **Log Archive:** `hackathon_logs_YYYYMMDD_HHMMSS.tar.gz`
2. **Analysis Report:** `log_analysis_report_YYYYMMDD_HHMMSS.md`
3. **Code Reference:** Link to `alphagenesis/sdm/sdm_engine.py` lines 189-915
4. **Status Reports:**
   - `STATUS_FOR_CODEX.md`
   - `VALIDATION_REPORT.md`
   - `CRITICAL_FIXES_COMPLETE.md`

### Submission Checklist

- [ ] Logs collected from production
- [ ] Analysis report generated
- [ ] All 6 fixes validated (or documented why not)
- [ ] Error count acceptable
- [ ] Trade history shows system is operational
- [ ] Risk gates showing decisions
- [ ] UTC timezone confirmed (if applicable)

---

## Troubleshooting

### Cannot Connect to GCP

**Issue:** `collect_logs.sh` fails with connection timeout

**Solution:**
```bash
# Test SSH connection
ssh root@34.133.16.230

# If fails, check:
# 1. VPN/network access
# 2. SSH key configured
# 3. IP address is correct
```

### No Log Files Found

**Issue:** Logs directory is empty

**Cause:** System might not be running on this instance

**Solution:**
```bash
# Check if service is running
ssh root@34.133.16.230 'systemctl status sdm-trading.service'

# Check if logs are in different location
ssh root@34.133.16.230 'find /opt /var/log -name "sdm_*.log" -o -name "trading*.log"'
```

### Missing Validation Evidence

**Issue:** Analysis shows warnings for missing validation data

**Causes:**
1. System hasn't generated signals yet
2. No positions opened (metrics would be zero)
3. Haven't crossed UTC midnight (no daily reset)

**Solution:**
- Wait for more trading activity
- Collect logs again after 24 hours
- Check that system is generating signals: `grep "SIGNAL" journal_full.log`

---

## Log Retention

**File Logs:** 30 days (automatic rotation)
**Journal Logs:** System default (usually 7 days)

**Recommendation:** Collect logs regularly during hackathon period to ensure comprehensive coverage.

---

## Contact

For issues with logging or validation:
1. Check `METADATA.txt` in log archive for analysis commands
2. Review `CRITICAL_FIXES_COMPLETE.md` for implementation details
3. Check GitHub issues if deployment problems

---

**Last Updated:** 2026-01-18
**Version:** 1.0
**Hackathon:** WEEX AI Wars: Alpha Awakens
