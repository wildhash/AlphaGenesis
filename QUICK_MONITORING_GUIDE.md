# Quick Monitoring Guide - Production Trading System

**For:** Codex (Production Deployment)
**Purpose:** Fast reference for monitoring the live trading system
**Updated:** 2026-01-31 05:26 UTC

---

## 🚀 IMMEDIATE START (30 seconds)

```bash
# 1. Check system is running
sudo systemctl status sdm-trading.service

# 2. Watch live trading activity
sudo journalctl -u sdm-trading.service -o cat -f | \
  egrep -i "DIAG_ACTION|WEEX_ORDER_RESPONSE|TIME STOP|BREAKOUT" --color=always

# 3. Run in separate terminal: 60-minute snapshot
cd /opt/AlphaGenesis && ./monitor_trade_performance.sh 60
```

---

## 📊 KEY METRICS TO WATCH

### Every 15 Minutes
```bash
# Quick health check
echo "Signals (last 15m): $(sudo journalctl -u sdm-trading.service -o cat --since '15 minutes ago' | grep -c 'DIAG_ACTION')"
echo "Orders (last 15m):  $(sudo journalctl -u sdm-trading.service -o cat --since '15 minutes ago' | grep -c 'WEEX_ORDER_RESPONSE')"
echo "Exits (last 15m):   $(sudo journalctl -u sdm-trading.service -o cat --since '15 minutes ago' | grep -c 'TIME STOP\|BREAKOUT')"
```

### Every 30 Minutes
```bash
# Run monitoring script
./monitor_trade_performance.sh 30
```

### Every 1-2 Hours
```bash
# Full outcome analysis
./analyze_trade_outcomes.sh 2
```

---

## 🚨 CRITICAL ALERTS

### RED FLAGS (Immediate Action)

**🔴 No signals for 30+ minutes**
```bash
# Diagnose
sudo journalctl -u sdm-trading.service -o cat --since "30 minutes ago" | grep -c "DIAG_ACTION"

# If 0, check for errors
sudo journalctl -u sdm-trading.service -o cat --since "30 minutes ago" | grep -i "error\|exception" | tail -10

# Emergency restart if needed
./emergency_unstall.sh
```

**🔴 Entries but NO exits**
```bash
# Check
entries=$(sudo journalctl -u sdm-trading.service -o cat --since "1 hour ago" | grep -c "DIAG_ACTION.*LONG\|DIAG_ACTION.*SHORT")
exits=$(sudo journalctl -u sdm-trading.service -o cat --since "1 hour ago" | grep -c "TIME STOP\|BREAKOUT\|AI_EXIT")

echo "Entries: $entries, Exits: $exits"

# If entries > 0 and exits = 0 for >30 minutes → EXIT LOGIC BROKEN
# Investigate exit mechanism immediately
```

**🔴 Continuous errors**
```bash
# Check error rate
sudo journalctl -u sdm-trading.service -o cat --since "15 minutes ago" | grep -c "Traceback\|Exception"

# If >5, review recent errors
sudo journalctl -u sdm-trading.service -o cat --since "15 minutes ago" | grep -iA 5 "Traceback\|Exception"
```

---

## 🟢 HEALTHY SYSTEM INDICATORS

### What Good Looks Like

**Signal Activity:**
- 5-15 signals per hour across 8 symbols
- Mix of LONG and SHORT directions
- Reasons logged (e.g., "Extreme reversal: RSI=14.0")

**Order Execution:**
- Every DIAG_ACTION followed by "Placing order:"
- Every order followed by WEEX_ORDER_RESPONSE
- Fill rate close to 100%

**Exit Pattern:**
- Mix of TIME STOP and BREAKOUT events
- Exits happening 15-45 minutes after entry
- BREAKOUT rate >35% (indicates profitable exits)

**Example Healthy Log Sequence:**
```
DIAG_ACTION | symbol=cmt_btcusdt | direction=LONG | reason='Extreme reversal: RSI=14.0 < 20'
Placing order: LONG cmt_btcusdt @ 45000 size=0.01
WEEX_ORDER_RESPONSE: order_id=123456 status=filled
[... 25 minutes later ...]
BREAKOUT: Closed LONG cmt_btcusdt @ 45850 | Profit: 1.89%
```

---

## 📈 P&L VERIFICATION

### Check Account Balance
```bash
# If check_weex_account.py exists
python3 scripts/check_weex_account.py

# Or check position ledger
cat /tmp/position_ledger.json | jq '.'
```

### Estimate Performance from Logs
```bash
# Count profitable vs unprofitable exits
breakouts=$(sudo journalctl -u sdm-trading.service -o cat --since "4 hours ago" | grep -c "BREAKOUT")
stops=$(sudo journalctl -u sdm-trading.service -o cat --since "4 hours ago" | grep -c "TIME STOP")

# Estimated win rate
echo "Breakouts: $breakouts, Stops: $stops"
if [ $((breakouts + stops)) -gt 0 ]; then
    win_rate=$((breakouts * 100 / (breakouts + stops)))
    echo "Estimated win rate: ${win_rate}%"
fi
```

---

## 🔧 TROUBLESHOOTING QUICK FIXES

### Signal Stall
```bash
# 1. Check bandit state
cat /tmp/bandit_state.json | jq '.'

# 2. If bandit looks stuck, reset
./emergency_unstall.sh

# 3. Monitor for signal recovery
sudo journalctl -u sdm-trading.service -o cat -f | grep "DIAG_ACTION"
```

### Exit Not Firing
```bash
# Check position monitor is running
sudo journalctl -u sdm-trading.service -o cat --since "5 minutes ago" | grep -i "position monitor"

# Check if positions exist
cat /tmp/position_ledger.json | jq '.positions'

# Restart service if needed
sudo systemctl restart sdm-trading.service
```

### High Error Rate
```bash
# Identify error pattern
sudo journalctl -u sdm-trading.service -o cat --since "30 minutes ago" | \
  grep -i "error\|exception" | \
  cut -d':' -f3 | sort | uniq -c | sort -rn | head -5

# Check WEEX API connectivity
# (Look for "WEEX_ORDER_RESPONSE" - if missing, API issue)
```

---

## 📋 HOURLY CHECKLIST

### Hour 1 (Initial Monitoring)
- [ ] System running (check service status)
- [ ] Signals generating (>5 in first hour)
- [ ] Orders filling (WEEX_ORDER_RESPONSE present)
- [ ] No critical errors
- [ ] First exits observed (verify exit logic works)

### Hour 2 (Performance Assessment)
- [ ] Run `./analyze_trade_outcomes.sh 2`
- [ ] Win rate >30%
- [ ] Realized P&L checked on WEEX
- [ ] Competition ranking checked
- [ ] No stuck positions (all <60 min)

### Hour 3+ (Optimization Decision)
- [ ] Sufficient data collected (>20 trades)
- [ ] Performance trend identified
- [ ] Decision: Continue current strategy OR adjust
- [ ] If adjusting: Make ONE change at a time
- [ ] If stable: Let it run, focus on competition ranking

---

## 🎯 COMPETITION RANKING STRATEGY

### Monitor Competitors
- Check WEEX AI Wars leaderboard every hour
- Track gap to 1st place
- Note what strategies seem to be working for leaders

### Adjust Based on Position
**If in 1st place:** Conservative - protect lead, avoid risky trades
**If in 2nd-3rd place:** Balanced - current strategy seems OK
**If falling:** Aggressive - consider threshold loosening or strategy change

### Final Hours Strategy
- Last 4 hours: Increase monitoring frequency to every 15 minutes
- Last 2 hours: Consider more aggressive position sizing if behind
- Last 1 hour: Risk management - don't blow up with big losses
- Last 30 min: Let open positions close naturally, avoid new entries

---

## 🛠️ COMMANDS CHEAT SHEET

```bash
# Service management
sudo systemctl status sdm-trading.service
sudo systemctl restart sdm-trading.service
sudo journalctl -u sdm-trading.service -o cat -f

# Monitoring
./monitor_trade_performance.sh [minutes]
./analyze_trade_outcomes.sh [hours]
./check_production_status.sh

# State files
cat /tmp/position_ledger.json | jq '.'
cat /tmp/bandit_state.json | jq '.'
sqlite3 /tmp/trading_journal.db "SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 10;"

# Emergency
./emergency_unstall.sh
sudo systemctl restart sdm-trading.service

# Real-time monitoring
sudo journalctl -u sdm-trading.service -o cat -f | \
  egrep -i "DIAG_ACTION|Placing order|WEEX_ORDER_RESPONSE|EXIT|STOP|BREAKOUT" --color=always
```

---

## 📞 DECISION TREE

```
Is system trading?
├─ NO → Check service status → Restart if needed → Check logs for errors
└─ YES
    ├─ Are signals generating?
    │   ├─ NO → Check for signal stall → Run emergency_unstall.sh
    │   └─ YES
    │       ├─ Are exits working?
    │       │   ├─ NO → CRITICAL: Investigate exit logic immediately
    │       │   └─ YES
    │       │       ├─ Is win rate >30%?
    │       │       │   ├─ NO → Analyze entry quality, consider adjustments
    │       │       │   └─ YES → Monitor and maintain current strategy
    │       │       └─ Is P&L positive?
    │       │           ├─ NO → Review strategy effectiveness
    │       │           └─ YES → Continue current approach, focus on ranking
```

---

**Remember:** The system is designed to trade autonomously. Your job is to MONITOR, not micromanage. Only intervene if critical issues arise or after collecting sufficient data to justify changes.

**Current Priority:** Verify exits are functioning, collect 1-2 hours of trade data, assess P&L.

**Good luck reclaiming 1st place! 🏆**
